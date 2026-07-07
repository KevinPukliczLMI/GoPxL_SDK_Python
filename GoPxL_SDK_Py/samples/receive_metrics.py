"""
Receive system metrics using REST streaming callbacks.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import sample_utils as su

SYSTEM_IP = "192.168.1.10"
CONTROL_PORT = 3600
ENGINE_ID = "LMILaserLineProfiler"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

PATHS = su.device_paths(ENGINE_ID, SCANNER_ID, SENSOR_ID)

SYSTEM_METRICS_PATH = "/system/metrics"
SCANNER_METRICS_PATH = f"{PATHS.scanner_path}/metrics"
SENSOR_METRICS_PATH = f"{PATHS.sensor_path}/metrics"
_print_lock = threading.Lock()


def _metric(payload: dict, key: str) -> object:
    value = payload.get(key)
    return "n/a" if value is None else value


def _on_metrics(notification) -> None:
    with _print_lock:
        payload = notification.payload or {}
        path = notification.path

        if path == SYSTEM_METRICS_PATH:
            print(f"\nApplication Uptime: {_metric(payload, 'appUpTime')}")
            print(f"CPU Cores Usage Average: {_metric(payload, 'cpuCoresUsedAvg')}")
            print(f"Memory Capacity: {_metric(payload, 'memCapacity')}")
            print(f"Memory Used: {_metric(payload, 'memUsed')}")

        elif path == SCANNER_METRICS_PATH:
            if "currentSyncTime" in payload:
                print(f"\nCurrent Sync Time: {_metric(payload, 'currentSyncTime')}")
                print(f"Frame Count: {_metric(payload, 'frameCount')}")
            elif "speed" in payload:
                print(f"\nCurrent Frame Rate: {_metric(payload, 'speed')}")
                print(f"Frame Count: {_metric(payload, 'scanCount')}")
            print(f"Processing Latency Average: {_metric(payload, 'processingLatencyAvg')}")
            print(f"Processing Latency Maximum: {_metric(payload, 'processingLatencyMax')}")

        elif path == SENSOR_METRICS_PATH:
            if "cameraTemp0" in payload:
                print(f"\nCamera Temperature 0: {_metric(payload, 'cameraTemp0')}")
                print(f"CPU Temperature: {_metric(payload, 'cpuTemp')}")
                print(f"Laser Driver Temperature: {_metric(payload, 'laserDriverTemp')}")
            elif "imagerTemp" in payload:
                print(f"\nImager Temperature: {_metric(payload, 'imagerTemp')}")
                print(f"Internal Temperature: {_metric(payload, 'intTemp')}")

        print(f"Type: {notification.type}")
        print(f"Status: {notification.status}")
        print(f"StreamId: {notification.stream_identifier}")
        print(f"StreamStatus: {notification.stream_status}")
        print(f"Path: {path}")


def _main(args):
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    client = system.client()
    stream_paths = (SYSTEM_METRICS_PATH, SCANNER_METRICS_PATH, SENSOR_METRICS_PATH)
    try:
        if system.running_state().name == "READY":
            print("\nStarting system...")
            system.start()
        client.set_stream_handler(_on_metrics)
        for path in stream_paths:
            client.start_stream(path).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        print("\nRunning callback to receive metrics...")
        print("Press Enter to stop streaming...")
        input()
    finally:
        for path in stream_paths:
            try:
                client.stop_stream(path).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
            except Exception:
                pass
        system.stop()
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Receive metrics via streaming API.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
