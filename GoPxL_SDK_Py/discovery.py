"""GoDiscoveryClient - mirrors GoPxLSdk::GoDiscoveryClient."""

from __future__ import annotations

import json
import platform
import re
import socket
import struct
import subprocess
import sys
import time

from .classic_discovery import discover_classic, parse_get_info_reply, parse_get_ip_reply, send_get_info
from .classic_discovery import GET_IP_REPLY_SIZE
from .def_ import DISCOVERY_UDP_PORT
from .instance import GoInstance

GOPXL_DISCOVERY_SIGNATURE = 0x4C58504F47494D4C  # "LMIGOPXL"
GOPXL_DISCOVERY_MESSAGE_DISCOVER = 0x0001
GOPXL_DISCOVERY_MESSAGE_ANNOUNCE = 0x1001
GOPXL_MAX_MESSAGE_SIZE = 1536


def _ipv4_from_os_interfaces() -> set[str]:
    """Enumerate IPv4 addresses from OS network tools (all Ethernet/Wi-Fi adapters)."""
    addresses: set[str] = set()
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    try:
        if platform.system() == "Windows":
            proc = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=creationflags,
                check=False,
            )
            text = proc.stdout or ""
            for match in re.finditer(r"IPv4[^:\r\n]*[:\s]+([\d.]+)", text, re.IGNORECASE):
                ip = match.group(1).strip()
                if ip and not ip.startswith("127."):
                    addresses.add(ip)
        else:
            proc = subprocess.run(
                ["ip", "-4", "-o", "addr", "show"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if proc.returncode == 0:
                for line in (proc.stdout or "").splitlines():
                    parts = line.split()
                    for token in parts:
                        if "/" in token and token.split("/")[0].count(".") == 3:
                            ip = token.split("/")[0]
                            if not ip.startswith("127."):
                                addresses.add(ip)
                            break
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return addresses


def ipv4_interface_addresses() -> list[str]:
    """Return local IPv4 addresses used for discovery broadcasts."""
    return _ipv4_interface_addresses()


def _ipv4_interface_addresses() -> list[str]:
    """Local IPv4 addresses to bind discovery senders (mirrors C++ kNetworkInfo)."""
    addresses: set[str] = set()
    addresses.update(_ipv4_from_os_interfaces())

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM):
            ip = info[4][0]
            if ip and not ip.startswith("127."):
                addresses.add(ip)
    except OSError:
        pass

    # Default-route probes (one per common gateway; does not cover every NIC).
    for probe_target in (("192.168.1.1", 1), ("192.168.0.1", 1), ("10.0.0.1", 1), ("8.8.8.8", 80)):
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                probe.connect(probe_target)
                ip = probe.getsockname()[0]
                if ip and not ip.startswith("127."):
                    addresses.add(ip)
            finally:
                probe.close()
        except OSError:
            continue

    return sorted(addresses)


def _make_udp_socket() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass
    return sock


def _directed_broadcasts(iface_ip: str) -> list[str]:
    """Best-effort /24 directed broadcasts for an interface address."""
    parts = iface_ip.split(".")
    if len(parts) != 4 or iface_ip.startswith("127."):
        return []
    try:
        if not all(0 <= int(p) <= 255 for p in parts):
            return []
    except ValueError:
        return []
    return [f"{parts[0]}.{parts[1]}.{parts[2]}.255"]


def _broadcast_discover(header: bytes, port: int) -> None:
    """Send discovery broadcast from each local interface, then from INADDR_ANY.

    Mirrors C++ GoPxLDiscoveryProto::Broadcast: bind a sender to each interface
    and send to 255.255.255.255. Also sends /24 directed broadcasts, which are
    more reliable on some Windows multi-homed setups.
    """
    targets = _ipv4_interface_addresses() + ["0.0.0.0"]
    seen: set[str] = set()
    for iface_ip in targets:
        if iface_ip in seen:
            continue
        seen.add(iface_ip)
        destinations = ["255.255.255.255"] + _directed_broadcasts(iface_ip)
        sender = _make_udp_socket()
        try:
            sender.bind((iface_ip, 0))
            for dest in destinations:
                try:
                    sender.sendto(header, (dest, port))
                except OSError:
                    continue
        except OSError:
            continue
        finally:
            sender.close()


class GoDiscoveryClient:
    def __init__(self) -> None:
        self._instances: list[GoInstance] = []
        self._gopxl_instances: list[GoInstance] = []
        self._classic_instances: list[GoInstance] = []

    def blocking_discover(self, timeout_ms: int = 3000, classic_discover: bool = False) -> None:
        self._instances.clear()
        self._gopxl_instances.clear()
        self._classic_instances.clear()

        self._discover_gopxl(timeout_ms)
        if classic_discover:
            self._discover_classic(timeout_ms)

        self._instances = list(self._gopxl_instances) + list(self._classic_instances)

    def _discover_gopxl(self, timeout_ms: int) -> None:
        # Matches DiscoveryBroadcastHeader: length, messageId, signature.
        header = struct.pack("<QQQ", 24, GOPXL_DISCOVERY_MESSAGE_DISCOVER, GOPXL_DISCOVERY_SIGNATURE)
        found: dict[tuple[str, int], GoInstance] = {}

        # C++ binds the receiver to UDP 3320 — sensors reply to that port, not the
        # ephemeral source port of the broadcast sender.
        receiver = _make_udp_socket()
        receiver.settimeout(0.25)
        try:
            try:
                receiver.bind(("", DISCOVERY_UDP_PORT))
            except OSError:
                # Port busy (another discovery client). Fall back to ephemeral and
                # also send from this socket so replies can return to it.
                receiver.bind(("", 0))

            _broadcast_discover(header, DISCOVERY_UDP_PORT)
            # Extra send from the receiver socket (covers single-interface cases).
            try:
                receiver.sendto(header, ("255.255.255.255", DISCOVERY_UDP_PORT))
            except OSError:
                pass

            end = time.monotonic() + timeout_ms / 1000.0
            while time.monotonic() < end:
                try:
                    data, _ = receiver.recvfrom(GOPXL_MAX_MESSAGE_SIZE)
                except socket.timeout:
                    continue
                except OSError:
                    break
                inst = self._parse_announce(data)
                if inst:
                    found[(inst.ip_address, inst.web_port)] = inst
        finally:
            receiver.close()

        self._gopxl_instances = sorted(found.values(), key=lambda i: i.ip_address)

    def _discover_classic(self, timeout_ms: int) -> None:
        self._classic_instances = discover_classic(timeout_ms)

    def instance_list(self) -> list[GoInstance]:
        return self._instances

    def gopxl_instance_list(self) -> list[GoInstance]:
        return self._gopxl_instances

    def classic_instance_list(self) -> list[GoInstance]:
        return self._classic_instances

    def instance(self, ip_address: str, web_port: int) -> GoInstance | None:
        for inst in self._instances:
            if inst.ip_address == ip_address and inst.web_port == web_port:
                return inst
        return None

    def gopxl_instance(self, ip_address: str, web_port: int) -> GoInstance | None:
        for inst in self._gopxl_instances:
            if inst.ip_address == ip_address and inst.web_port == web_port:
                return inst
        return None

    def classic_instance(self, serial_number: int) -> GoInstance | None:
        for inst in self._classic_instances:
            if str(inst.serial_number) == str(serial_number):
                return inst
        return None

    def parse_reply(self, data: bytes) -> None:
        if len(data) == GET_IP_REPLY_SIZE:
            inst = parse_get_ip_reply(data)
            if inst is None:
                return
            serial = int(inst.serial_number)
            if any(str(i.serial_number) == str(serial) for i in self._classic_instances):
                return
            self._classic_instances.append(inst)
            self._instances.append(inst)
            sock = _make_udp_socket()
            try:
                send_get_info(sock, serial)
            finally:
                sock.close()
            return

        pending = {int(i.serial_number): i for i in self._classic_instances}
        inst = parse_get_info_reply(data, pending)
        if inst is None:
            gopxl = self._parse_announce(data)
            if gopxl is None:
                return
            key = (gopxl.ip_address, gopxl.web_port)
            if not any(i.ip_address == key[0] and i.web_port == key[1] for i in self._gopxl_instances):
                self._gopxl_instances.append(gopxl)
                self._instances.append(gopxl)
            return

        for idx, existing in enumerate(self._classic_instances):
            if str(existing.serial_number) == str(inst.serial_number):
                self._classic_instances[idx] = inst
                break

    @staticmethod
    def _parse_announce(data: bytes) -> GoInstance | None:
        # DiscoveryServerHeader is 32 bytes: length, messageId, signature, messageStatus.
        if len(data) < 32:
            return None
        _length, message_id, signature = struct.unpack_from("<QQQ", data, 0)
        if message_id == GOPXL_DISCOVERY_MESSAGE_DISCOVER:
            return None
        if message_id != GOPXL_DISCOVERY_MESSAGE_ANNOUNCE or signature != GOPXL_DISCOVERY_SIGNATURE:
            return None
        try:
            text = data[32:].decode("utf-8", errors="replace").split("\x00", 1)[0].strip()
            if not text:
                return None
            payload = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            return None
        return GoInstance.from_announce(payload)
