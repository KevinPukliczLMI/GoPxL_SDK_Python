"""
Demonstrates comprehensive sensor configuration (triggers, exposure, I/O).

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

SOFTWARE_TRIGGER_MODE = 3
SINGLE_EXPOSURE_MODE = 0
MULTI_EXPOSURE_MODE = 1
TRIGGER_PATH = f"{su.SCANNER_PATH}/actions/trigger"
DIGITAL_OUTPUT_PORT = f"{su.DIGITAL_OUTPUT_PATH}/devices/device-0/ports/port-0"
DIO_TRIGGER_EVENTS = {
    1: "Measurement",
    2: "Software",
    3: "Alignment",
    4: "Exposure Begin",
    5: "Exposure End",
    6: "Part Detection",
    7: "System State",
}


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
        su.print_section("Configuration 1: Update trigger source.")
        payload = {"parameters": {"triggerSettings": {"source": SOFTWARE_TRIGGER_MODE}}}
        client.update(su.SCANNER_PATH, payload).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        system.start()
        client.call(TRIGGER_PATH).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        system.stop()

        su.print_section("Configuration 2: Update single exposure.")
        payload = {
            "parameters": {
                "exposureSettings": {
                    "exposureMode": SINGLE_EXPOSURE_MODE,
                    "singleExposure": 1200,
                }
            }
        }
        client.update(su.SENSOR_PATH, payload).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        exposure = (
            client.read(su.SENSOR_PATH).get_response().payload.get("parameters", {})
            .get("exposureSettings", {}).get("singleExposure")
        )
        print(f"Exposure value: {exposure}")

        su.print_section("Configuration 3: Update multiple exposures.")
        payload = {
            "parameters": {
                "exposureSettings": {
                    "exposureMode": MULTI_EXPOSURE_MODE,
                    "multipleExposures": [1080, 2010, 5040],
                }
            }
        }
        client.update(su.SENSOR_PATH, payload).check_response(su.REST_COMMAND_TIMEOUT_MSEC)

        su.print_section("Configuration 4: Update sensor name.")
        client.update(su.SENSOR_PATH, {"displayName": "Main-Sensor-Change"}).check_response(
            su.REST_COMMAND_TIMEOUT_MSEC
        )

        su.print_section("Configuration 5: Change the active area.")
        client.update(
            su.SENSOR_PATH,
            {"parameters": {"activeAreaSettings": {"activeArea": {"width": 3.5}}}},
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)

        su.print_section("Configuration 6: Enable, trigger, and configure Digital Output.")
        client.update(su.DIGITAL_OUTPUT_PATH, {"enabled": True}).check_response(
            su.REST_COMMAND_TIMEOUT_MSEC
        )
        devices = client.read(f"{su.DIGITAL_OUTPUT_PATH}/devices").get_response().payload
        if "_embedded" not in devices:
            avail = client.read(f"{su.DIGITAL_OUTPUT_PATH}/availableDevices").get_response().payload
            device_list = avail.get("devices") or []
            if device_list:
                client.create(f"{su.DIGITAL_OUTPUT_PATH}/devices", device_list[0]).check_response(
                    su.REST_COMMAND_TIMEOUT_MSEC
                )
        client.update(DIGITAL_OUTPUT_PORT, {"parameters": {"triggerEvent": 2}}).check_response(
            su.REST_COMMAND_TIMEOUT_MSEC
        )
        event = (
            client.read(DIGITAL_OUTPUT_PORT).get_response().payload.get("parameters", {}).get("triggerEvent")
        )
        print(f"Digital output trigger event: {DIO_TRIGGER_EVENTS.get(int(event or 0), event)}")
        try:
            client.call(
                f"{DIGITAL_OUTPUT_PORT}/commands/trigger",
                {"parameter": {"target": 0, "value": True}},
            ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        except Exception as exc:
            print(f"Note: digital output pulse failed: {exc}")
        client.update(
            DIGITAL_OUTPUT_PORT,
            {"parameters": {"signalType": 1, "scheduled": True}},
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)

        su.print_section("Configuration 7: Read network configuration.")
        interfaces = client.read(su.IP_CONFIG_PATH).get_response().payload.get("interfaces")
        print(f"Network configurations: {interfaces}.")
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Configure sensor parameters via REST.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
