"""
Create and configure tools using GoResource helpers.

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
def _main(args):
    from gopxl_sdk import GoSystem
    import time

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    try:
        tools = system.resource("/tools")
        tool = tools.create_child({"type": su.TOOL_TYPE})
        print(f"Tool created at: {tool.uri()}")

        tool.set_string("/extId", su.TOOL_ID)
        if not tool.get_bool("/parameters/UseRegion"):
            tool.set_bool("/parameters/UseRegion", True)

        with tool.scoped_update():
            tool.set_double("/parameters/Region/height", 10.0)
            tool.set_double("/parameters/Region/width", 10.0)
            tool.set_double("/parameters/Region/x", 5.0)
            tool.set_double("/parameters/Region/z", 5.0)

        data_sources = system.resource("/dataSources")
        print("Data sources:")
        for uri in data_sources.child_uris():
            print(f"  {uri}")

        profile_input = tool.child("inputs/ProfileInput")
        profile_input.set_string("/dataSource", su.TOP_UNIFORM_PROFILE)

        output = tool.child(f"outputs/{su.TOOL_OUTPUT_NAME}")
        output.set_bool("/enabled", True)

        time.sleep(1)
        metrics = tool.child("metrics")
        try:
            print(f"Measurement value: {metrics.get_prop('/outputsByExtId/X/value')}")
        except Exception as exc:
            print(f"Note: could not read metrics ({exc})")

        gocator = system.resource(su.GOCATOR_CONTROL_PATH)
        gocator.set_bool("/enabled", True)
        add_outputs = system.resource(su.GOCATOR_ADD_OUTPUT_PATH)
        add_outputs.call(
            {
                "source": su.TOOL_OUTPUT_DATA_PATH,
                "outputId": 1,
                "autoShift": True,
            }
        )
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Configure tool via GoResource.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
