"""
Receive system metrics using REST streaming callbacks.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

SYSTEM_IP = "192.168.1.10"
CONTROL_PORT = 3600

import threading

SYSTEM_METRICS_PATH = "/system/metrics"
SCANNER_METRICS_PATH = f"{su.SCANNER_PATH}/metrics"
SENSOR_METRICS_PATH = f"{su.SENSOR_PATH}/metrics"
_print_lock = threading.Lock()


def _on_metrics(notification) -> None:
    with _print_lock:
        payload = getattr(notification, "payload", {}) or {}
        print(f"Path: {getattr(notification, 'path', '')}")
        print(f"Payload keys: {list(payload.keys())[:8]}")


def _main(args):
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    client = system.client()
    try:
        gh.start_if_ready(system)
        client.set_stream_handler(_on_metrics)
        client.start_stream(SYSTEM_METRICS_PATH)
        client.start_stream(SCANNER_METRICS_PATH)
        client.start_stream(SENSOR_METRICS_PATH)
        print("\nStreaming metrics. Press Enter to stop...")
        input()
    finally:
        system.stop()
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Receive metrics via streaming API.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
