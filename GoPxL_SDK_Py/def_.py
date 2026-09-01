"""Constants from GoPxLSdk Def.h."""

from __future__ import annotations

import socket

DEFAULT_TCP_TIMEOUT_MILLISECONDS = 1000
DEFAULT_CONTROL_PORT = 3600
DEFAULT_GDP_SERVER_PORT = 3601
DEFAULT_WEB_PORT = 8100
DISCOVERY_UDP_PORT = 3320

MSGPACK_MESSAGE_TYPE = 0xB000
JSON_MESSAGE_TYPE = 0xB001

DEFAULT_TRANSACTION_TIMEOUT_MSEC = 3000


def configure_tcp_socket(
    sock: socket.socket,
    *,
    keepalive_idle_ms: int = 15000,
    keepalive_interval_ms: int = 2000,
) -> None:
    """Reduce latency and detect dead peers so control/GDP sockets stay healthy."""
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError:
        pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    except OSError:
        pass
    if hasattr(socket, "SIO_KEEPALIVE_VALS"):
        try:
            sock.ioctl(
                socket.SIO_KEEPALIVE_VALS,
                (1, int(keepalive_idle_ms), int(keepalive_interval_ms)),
            )
            return
        except OSError:
            pass
    idle_s = max(1, int(keepalive_idle_ms / 1000))
    intvl_s = max(1, int(keepalive_interval_ms / 1000))
    if hasattr(socket, "TCP_KEEPIDLE"):
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, idle_s)
        except OSError:
            pass
    elif hasattr(socket, "TCP_KEEPALIVE"):
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPALIVE, idle_s)
        except OSError:
            pass
    if hasattr(socket, "TCP_KEEPINTVL"):
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, intvl_s)
        except OSError:
            pass
    if hasattr(socket, "TCP_KEEPCNT"):
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
        except OSError:
            pass
