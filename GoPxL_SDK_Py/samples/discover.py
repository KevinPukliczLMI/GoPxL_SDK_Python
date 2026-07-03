"""
Discover sensors and GoPxL instances on the network.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

def main() -> int:
    su.bootstrap_sdk()
    from gopxl_sdk import GoDiscoveryClient, GoSystem
    from gopxl_sdk.exceptions import GoRequestError

    discovery = GoDiscoveryClient()
    discovery.blocking_discover(su.DISCOVER_TIMEOUT_MSEC, classic_discover=False)
    instances = discovery.instance_list()
    print(f"Number of sensors on the network: {len(instances)}")
    if not instances:
        print("No sensors found. Make sure sensors or GoPxL on PC/GoMax are available and connected.")
        return su.ERROR_STATUS

    for index, inst in enumerate(instances, start=1):
        name = inst.app_name or inst.app_id
        print("\n" + "*" * 52 + f" GoPxL instance {index}: '{name}'")
        print(f"Is remote: {'Yes' if inst.is_remote else 'No'}")
        print(f"IP Address: {inst.ip_address}")
        print(f"Control Port: {inst.control_port}")
        if inst.is_remote:
            continue
        system = GoSystem(inst.ip_address, inst.control_port or su.DEFAULT_CONTROL_PORT)
        if su.connect_system(system, inst.ip_address, inst.control_port or su.DEFAULT_CONTROL_PORT):
            return su.ERROR_STATUS
        try:
            sensors = (
                system.client().read(su.VISIBLE_SENSORS_PATH).get_response().payload.get("sensors", [])
            )
            for sensor_index, sensor in enumerate(sensors, start=1):
                serial = str(sensor.get("serialNumber", ""))
                sensor_path = system.sensor_path(serial)
                if not sensor_path:
                    continue
                print("\n" + "*" * 22 + f" Sensor {sensor_index}: {serial} -> {sensor_path}")
        except GoRequestError as exc:
            print(f"Error: {su.format_request_error(exc)}")
        finally:
            system.disconnect()
    return su.OK_STATUS


if __name__ == "__main__":
    raise SystemExit(main())
