"""
Add and configure a Profile Bounding Box tool.

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
        create_payload = {"type": su.TOOL_TYPE, "autoConnect": False, "position": 0}
        print(f"\nAdding new tool: {su.TOOL_TYPE}...")
        client.create(su.TOOLS_PATH, create_payload).check_response(su.REST_COMMAND_TIMEOUT_MSEC)

        tools = client.read(su.TOOLS_PATH).get_response().payload
        items = (tools.get("_embedded") or {}).get("item") or []
        if not items:
            print("Failed to locate created tool.")
            return su.ERROR_STATUS
        tool_path = str(items[0].get("_links", {}).get("self", {}).get("href", "")).strip("/")
        if tool_path.startswith("./"):
            tool_path = tool_path[2:]

        tool = client.read(tool_path).get_response().payload
        if not tool.get("parameters", {}).get("UseRegion"):
            print("\nEnabling tool region...")
            client.update(tool_path, {"parameters": {"UseRegion": True}}).check_response(
                su.REST_COMMAND_TIMEOUT_MSEC
            )
        client.update(tool_path, {"extId": su.TOOL_ID}).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        client.update(
            su.TOOL_PATH,
            {
                "parameters": {
                    "Region": {"height": 10.0, "width": 10.0, "x": 5.0, "z": 5.0},
                }
            },
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)

        client.update(su.PROFILE_INPUT_PATH, {"dataSource": su.TOP_UNIFORM_PROFILE}).check_response(
            su.REST_COMMAND_TIMEOUT_MSEC
        )
        client.update(f"{su.TOOL_PATH}/outputs/{su.TOOL_OUTPUT_NAME}", {"enabled": True}).check_response(
            su.REST_COMMAND_TIMEOUT_MSEC
        )
        gh.enable_gocator_protocol(system)
        gh.add_gdp_output(system, f'"{su.TOOL_OUTPUT_DATA_PATH}"', output_id=1)
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Configure a measurement tool.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
