"""
Discover sensors and GoPxL instances on the network.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import sample_utils as su

DISCOVER_TIMEOUT_MSEC = 5000


def main() -> int:
    su.bootstrap_sdk()
    from gopxl_sdk import GoDiscoveryClient, GoSystem
    from gopxl_sdk.discovery import ipv4_interface_addresses
    from gopxl_sdk.exceptions import GoRequestError

    ifaces = ipv4_interface_addresses()
    print(f"Discovering on local interfaces: {', '.join(ifaces) if ifaces else '(none found)'}")
    print("Broadcasting on UDP 3320 (GoPxL) and 3220 (classic Gocator)...")

    discovery = GoDiscoveryClient()
    discovery.blocking_discover(DISCOVER_TIMEOUT_MSEC, classic_discover=True)
    instances = discovery.instance_list()
    print(f"\nNumber of sensors on the network: {len(instances)}")
    if not instances:
        print(
            "No sensors found. Ensure the PC and sensor share a subnet, "
            "disable VPN if needed, and allow UDP 3320/3220 in the firewall."
        )
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
