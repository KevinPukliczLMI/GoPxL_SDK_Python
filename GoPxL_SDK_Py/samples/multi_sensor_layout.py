"""
Configure a multi-sensor scanner layout.

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
ENGINE_ID = "LMILaserLineProfiler"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

PATHS = su.device_paths(ENGINE_ID, SCANNER_ID, SENSOR_ID)

SCANNERS_PATH = f"{PATHS.engine_path}/scanners"
SENSOR_2_SERIAL = "62984"


def _main(args):
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    if ENGINE_ID != "LMILaserLineProfiler":
        print("Multi-sensor layout requires LMILaserLineProfiler.")
        system.disconnect()
        return su.ERROR_STATUS
    client = system.client()
    try:
        engine = client.read(PATHS.engine_path).get_response().payload
        embedded = (engine.get("_embedded") or {}).get("go:scanner")
        if not embedded:
            print("\nScanner not present, creating scanner...")
            client.create(SCANNERS_PATH).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        client.create(
            f"{SCANNERS_PATH}/{su.SCANNER_ID}/sensors",
            {"serialNumber": SENSOR_2_SERIAL},
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        layout = client.read(f"{SCANNERS_PATH}/{su.SCANNER_ID}/layout").get_response().payload
        sensors = (layout.get("grid") or {}).get("sensors") or []
        print("\nSensor layout:")
        for entry in sensors:
            print(
                f"  id={entry.get('sensorId')} row={entry.get('row')} col={entry.get('column')} "
                f"orientation={entry.get('orientation')}"
            )
    except Exception as exc:
        print(f"Layout update failed: {exc}")
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Configure multi-sensor layout.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
