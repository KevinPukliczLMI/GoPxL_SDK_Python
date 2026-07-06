"""
Demonstrate GoResource subscriptions, caching, and child enumeration.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common import gdp_helpers as gh
from common import sample_utils as su

SYSTEM_IP = "192.168.1.10"
CONTROL_PORT = 3600
ENGINE_ID = "2dscanner"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

PATHS = su.device_paths(ENGINE_ID, SCANNER_ID, SENSOR_ID)ENGINE_ID = "2dscanner"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

PATHS = su.device_paths(ENGINE_ID, SCANNER_ID, SENSOR_ID)
import time


def _main(args):
    from gopxl_sdk import GoSystem
    from gopxl_sdk.resource import GoRelationType

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    try:
        system_res = system.resource("/system")
        system_res.subscribe()
        print(f"IsSubscribed: {system_res.is_subscribed()}")
        run_state = system_res.get_int("/runState")
        print(f"Initial runState: {run_state}")
        system.start()
        time.sleep(0.5)
        print(f"HasRemoteChanges after start: {system_res.has_remote_changes()}")
        print(f"Updated runState: {system_res.get_int('/runState')}")
        system.stop()
        time.sleep(0.5)
        system_res.unsubscribe()

        system.resource_manager().set_auto_subscribe(True)
        sensor = system.resource(PATHS.sensor_path)
        sensor.cache()
        print(f"Sensor subscribed: {sensor.is_subscribed()}")
        system.resource_manager().set_auto_subscribe(False)

        engines = system.resource("/scan/engines")
        engines.set_expand_level(0)
        engines.cache()
        print("Engines (expand 0):", engines.child_uris())
        engines.set_expand_level(1)
        engines.invalidate_cache()
        engines.cache()
        print("Engines (expand 1):", [c.uri() for c in engines.children()])

        laser = system.resource(su.ENGINE_PATH)
        laser.set_expand_level(1)
        print("Scanners:", laser.child_uris(GoRelationType.Scanner))

        info = system.resource("/system/info")
        app_id = info.get_string("/appId")
        print(f"appId (cached): {app_id}")
        info.invalidate_cache()
        print(f"appId (refreshed): {info.get_string('/appId')}")

        if sensor.is_subscribed():
            sensor.unsubscribe()
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("GoResource subscriptions sample.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
