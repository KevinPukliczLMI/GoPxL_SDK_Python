"""
Receive system metrics using REST streaming callbacks.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

SYSTEM_METRICS_PATH = "/system/metrics"
_print_lock = threading.Lock()
_paths: dict[str, str] = {}


def _get(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Return the first present key (supports leading '/' like C++ JSON pointers)."""
    for key in keys:
        bare = key.lstrip("/")
        if bare in payload:
            return payload[bare]
        if key in payload:
            return payload[key]
    return default


def _on_metrics(notification) -> None:
    with _print_lock:
        payload = getattr(notification, "payload", {}) or {}
        if not isinstance(payload, dict):
            payload = {}
        path = str(getattr(notification, "path", "") or "")

        system_path = _paths.get("system", SYSTEM_METRICS_PATH)
        scanner_path = _paths.get("scanner", "")
        sensor_path = _paths.get("sensor", "")

        if path == system_path or path.rstrip("/") == system_path.rstrip("/"):
            print("\n--- System metrics ---")
            print(f"Application Uptime: {_get(payload, 'appUpTime', default='n/a')}")
            print(f"CPU Cores Usage Average: {_get(payload, 'cpuCoresUsedAvg', default='n/a')}")
            print(f"Memory Capacity: {_get(payload, 'memCapacity', default='n/a')}")
            print(f"Memory Used: {_get(payload, 'memUsed', default='n/a')}")
        elif scanner_path and (
            path == scanner_path or path.rstrip("/") == scanner_path.rstrip("/")
        ):
            print("\n--- Scanner metrics ---")
            # Laser profiler fields
            sync = _get(payload, "currentSyncTime")
            frames = _get(payload, "frameCount")
            # SmartCam fields
            speed = _get(payload, "speed")
            scans = _get(payload, "scanCount")
            if sync is not None:
                print(f"Current Sync Time: {sync}")
            if frames is not None:
                print(f"Frame Count: {frames}")
            if speed is not None:
                print(f"Current Frame Rate: {speed}")
            if scans is not None:
                print(f"Frame Count: {scans}")
            print(
                f"Processing Latency Average: "
                f"{_get(payload, 'processingLatencyAvg', default='n/a')}"
            )
            print(
                f"Processing Latency Maximum: "
                f"{_get(payload, 'processingLatencyMax', default='n/a')}"
            )
        elif sensor_path and (
            path == sensor_path or path.rstrip("/") == sensor_path.rstrip("/")
        ):
            print("\n--- Sensor metrics ---")
            # Laser profiler fields
            cam0 = _get(payload, "cameraTemp0")
            cpu = _get(payload, "cpuTemp")
            laser = _get(payload, "laserDriverTemp")
            # SmartCam fields
            imager = _get(payload, "imagerTemp")
            internal = _get(payload, "intTemp")
            if cam0 is not None:
                print(f"Camera Temperature 0: {cam0}")
            if cpu is not None:
                print(f"CPU Temperature: {cpu}")
            if laser is not None:
                print(f"Laser Driver Temperature: {laser}")
            if imager is not None:
                print(f"Imager Temperature: {imager}")
            if internal is not None:
                print(f"Internal Temperature: {internal}")
            # Always show something if none of the known keys were present.
            if all(v is None for v in (cam0, cpu, laser, imager, internal)):
                for key, value in list(payload.items())[:12]:
                    if key.startswith("_"):
                        continue
                    print(f"{key}: {value}")
        else:
            print(f"\n--- Metrics ({path}) ---")
            for key, value in list(payload.items())[:12]:
                if key.startswith("_"):
                    continue
                print(f"{key}: {value}")

        print(f"Type: {getattr(notification, 'type', '')}")
        print(f"Status: {getattr(notification, 'status', '')}")
        print(f"StreamId: {getattr(notification, 'stream_identifier', '')}")
        print(f"StreamStatus: {getattr(notification, 'stream_status', '')}")
        print(f"Path: {path}")


def _main(args) -> int:
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS

    client = system.client()
    engine_id = su.resolve_engine_id(system)
    scanner_metrics = f"{su.scanner_path_for(engine_id)}/metrics"
    sensor_metrics = f"{su.sensor_path_for(engine_id)}/metrics"
    _paths["system"] = SYSTEM_METRICS_PATH
    _paths["scanner"] = scanner_metrics
    _paths["sensor"] = sensor_metrics
    print(f"\nUsing scan engine: {engine_id}")
    print(f"Scanner metrics: {scanner_metrics}")
    print(f"Sensor metrics:  {sensor_metrics}")

    streams = [SYSTEM_METRICS_PATH, scanner_metrics, sensor_metrics]
    try:
        gh.start_if_ready(system)
        print("\nRunning callback to receive metrics...")
        print("Press Enter to close the connection and exit.")
        client.set_stream_handler(_on_metrics)
        for path in streams:
            client.start_stream(path).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        input()
    finally:
        for path in streams:
            try:
                client.stop_stream(path).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
            except Exception:
                pass
        try:
            system.stop()
        except Exception:
            pass
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Receive metrics via streaming API.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
