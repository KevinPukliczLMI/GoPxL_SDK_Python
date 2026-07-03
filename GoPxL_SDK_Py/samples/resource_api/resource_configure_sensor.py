"""
Configure scanner/sensor using typed GoResource setters.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common import gdp_helpers as gh
from common import sample_utils as su

SOFTWARE_TRIGGER_MODE = 3
SINGLE_EXPOSURE_MODE = 0
MULTI_EXPOSURE_MODE = 1


def _main(args):
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    try:
        scanner = system.resource(su.SCANNER_PATH)
        sensor = system.resource(su.SENSOR_PATH)

        su.print_section("Configuration 1: Update trigger source.")
        scanner.set_int("/parameters/triggerSettings/source", SOFTWARE_TRIGGER_MODE)
        print(f"Trigger source: {scanner.get_int('/parameters/triggerSettings/source')}")
        system.start()
        scanner.call_action("trigger")
        system.stop()

        su.print_section("Configuration 2: Update single exposure.")
        with sensor.scoped_update():
            sensor.set_int("/parameters/exposureSettings/exposureMode", SINGLE_EXPOSURE_MODE)
            sensor.set_int("/parameters/exposureSettings/singleExposure", 1200)
        print(f"Exposure: {sensor.get_int('/parameters/exposureSettings/singleExposure')}")

        su.print_section("Configuration 3: Update multiple exposures.")
        with sensor.scoped_update():
            sensor.set_int("/parameters/exposureSettings/exposureMode", MULTI_EXPOSURE_MODE)
            sensor.set_prop(
                "/parameters/exposureSettings/multipleExposures",
                [1080, 2010, 5040],
            )
        print(f"Multi exposures: {sensor.get_prop('/parameters/exposureSettings/multipleExposures')}")

        su.print_section("Configuration 4: Update sensor name.")
        sensor.set_string("/displayName", "Main-Sensor-Change")
        print(f"Display name: {sensor.get_string('/displayName')}")

        su.print_section("Configuration 5: Change the active area.")
        sensor.set_double("/parameters/activeAreaSettings/activeArea/width", 3.5)
        print(f"Active area: {sensor.get_object('/parameters/activeAreaSettings/activeArea')}")
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Configure sensor via GoResource.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
