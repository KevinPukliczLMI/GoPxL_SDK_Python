"""GoGdpClient - mirrors GoPxLSdk::GoGdpClient."""

from __future__ import annotations

import queue
import socket
import threading
from typing import Callable

from .def_ import DEFAULT_GDP_SERVER_PORT
from .dataset import GoDataSet
from .exceptions import GoChannelError
from .gdp_msg import GoGdpMsg, parse_gdp_message
from .kserializer import read_gdp_packet

# Sentinel placed on the data queue to stop the callback thread.
_QUEUE_STOP = object()


class GoGdpClient:
    def __init__(self) -> None:
        self._sock: socket.socket | None = None
        self._connected = False
        self._async = False
        self._receive_thread: threading.Thread | None = None
        self._data_thread: threading.Thread | None = None
        self._data_queue: queue.Queue | None = None
        self._callback: Callable[[GoDataSet], None] | None = None
        self._dataset = GoDataSet()
        self._ip_address: str = ""
        self._port: int = 0

    def connect(self, ip_address: str, port: int = DEFAULT_GDP_SERVER_PORT, timeout: float = 5.0) -> None:
        if self._connected:
            self.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((ip_address, port))
        except OSError as exc:
            sock.close()
            raise GoChannelError(f"Failed to connect GDP to {ip_address}:{port}: {exc}") from exc
        sock.settimeout(1.0)
        self._sock = sock
        self._connected = True
        self._ip_address = ip_address
        self._port = port

    def close(self) -> None:
        self._async = False
        self._connected = False
        if self._sock:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        if self._data_queue is not None:
            try:
                self._data_queue.put_nowait(_QUEUE_STOP)
            except Exception:
                pass
        if self._receive_thread and self._receive_thread.is_alive():
            self._receive_thread.join(timeout=2.0)
        if self._data_thread and self._data_thread.is_alive():
            self._data_thread.join(timeout=2.0)
        self._receive_thread = None
        self._data_thread = None
        self._data_queue = None

    def is_connected(self) -> bool:
        return self._connected and self._sock is not None

    def ip_address(self) -> str:
        return self._ip_address

    def port(self) -> int:
        return self._port

    def dataset(self) -> GoDataSet:
        return self._dataset

    def clear_data(self) -> None:
        self._dataset.clear()

    def receive_data_sync(self, timeout_ms: int = 20000) -> None:
        if not self.is_connected() or not self._sock:
            raise GoChannelError("Not connected")
        if self._async:
            raise GoChannelError("Cannot receive synchronously while async receive is active")
        self._dataset.clear()
        self._dataset.set_sender(self)
        deadline = timeout_ms / 1000.0
        remaining = deadline
        while self.is_connected():
            if remaining <= 0:
                raise GoChannelError("GDP receive timed out")
            try:
                msg_type, packet = read_gdp_packet(self._sock)
                try:
                    msg = parse_gdp_message(msg_type, packet)
                except EOFError as exc:
                    raise EOFError(
                        f"{exc} (message type={msg_type}, packet size={len(packet)})"
                    ) from exc
                self._dataset.add(msg)
                if isinstance(msg, GoGdpMsg) and msg.is_last_msg():
                    return
            except socket.timeout:
                remaining -= 1.0
                continue
            except EOFError as exc:
                if "connection closed" in str(exc).lower():
                    self._connected = False
                raise GoChannelError(str(exc)) from exc

    def receive_data_async(self, callback: Callable[[GoDataSet], None]) -> None:
        """Receive GDP datasets on a background thread and invoke *callback* on another.

        Mirrors C++ GoGdpClient::ReceiveDataAsync: a receive thread reads the socket
        and enqueues complete datasets; a data thread dequeues and runs the callback.
        Slow callbacks no longer block socket reads.
        """
        if not self.is_connected():
            raise GoChannelError("Not connected")
        if self._async:
            raise GoChannelError("Async receive already active")
        self._callback = callback
        self._async = True
        self._data_queue = queue.Queue()
        self._receive_thread = threading.Thread(
            target=self._receive_loop, daemon=True, name="GoGdpClient-recv"
        )
        self._data_thread = threading.Thread(
            target=self._data_loop, daemon=True, name="GoGdpClient-data"
        )
        self._receive_thread.start()
        self._data_thread.start()

    def _receive_loop(self) -> None:
        """Read packets from the socket and enqueue complete datasets."""
        dataset = GoDataSet()
        dataset.set_sender(self)
        try:
            while self.is_connected() and self._async and self._sock is not None:
                try:
                    msg_type, packet = read_gdp_packet(self._sock)
                    msg = parse_gdp_message(msg_type, packet)
                    dataset.add(msg)
                    if isinstance(msg, GoGdpMsg) and msg.is_last_msg():
                        if self._data_queue is not None:
                            self._data_queue.put(dataset)
                        dataset = GoDataSet()
                        dataset.set_sender(self)
                except socket.timeout:
                    continue
                except EOFError:
                    self._connected = False
                    break
                except OSError:
                    self._connected = False
                    break
        finally:
            if self._data_queue is not None:
                try:
                    self._data_queue.put(_QUEUE_STOP)
                except Exception:
                    pass

    def _data_loop(self) -> None:
        """Dequeue datasets and invoke the user callback."""
        while self._async:
            if self._data_queue is None:
                break
            try:
                item = self._data_queue.get(timeout=0.1)
            except queue.Empty:
                if not self.is_connected() and not self._async:
                    break
                continue
            if item is _QUEUE_STOP:
                break
            dataset = item
            self._dataset = dataset
            if self._callback is not None:
                try:
                    self._callback(dataset)
                except Exception:
                    # Match C++: log and continue receiving.
                    pass
