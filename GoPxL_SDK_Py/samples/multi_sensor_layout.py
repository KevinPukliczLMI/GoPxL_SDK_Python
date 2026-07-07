"""
Configure a multi-sensor scanner layout across laser line profilers.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.

Requires multiple LMILaserLineProfiler sensors on the network with compatible
firmware. Connect to the master profiler; additional profilers are added to the
group by serial number (read from each profiler IP, or set explicitly below).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import sample_utils as su

CONTROL_PORT = 3600
ENGINE_ID = "LMILaserLineProfiler"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

# Master profiler — hosts the sensor group (REST connection target).
MASTER_SENSOR_IP = "192.168.1.10"

# Other profilers on the network to add to the group.
ADDITIONAL_PROFILER_IPS = [
    "192.168.1.11",
]

# Optional: set serials directly instead of reading them from ADDITIONAL_PROFILER_IPS.
# Leave empty to auto-read serial numbers from each additional profiler.
ADDITIONAL_SENSOR_SERIALS: list[str] = []

PATHS = su.device_paths(ENGINE_ID, SCANNER_ID, SENSOR_ID)
SCANNERS_PATH = f"{PATHS.engine_path}/scanners"
SENSORS_PATH = f"{PATHS.scanner_path}/sensors"
LAYOUT_PATH = f"{PATHS.scanner_path}/layout"


def _read_profiler_serial(ip: str, port: int) -> str:
    """Connect to a profiler and return sensor-0 serial number."""
    from gopxl_sdk import GoSystem
    from gopxl_sdk.exceptions import GoRequestError

    system = GoSystem()
    system.set_address(ip)
    system.set_control_port(port)
    print(f"\nReading serial from profiler at {ip}:{port}...")
    try:
        system.connect()
        sensor = (
            system.client()
            .read(PATHS.sensor_path)
            .get_response(su.REST_COMMAND_TIMEOUT_MSEC)
            .payload
        )
        serial = str(sensor.get("serialNumber", "")).strip()
        if not serial:
            raise GoRequestError(f"No serial number at {PATHS.sensor_path}", response=None)
        print(f"  serial={serial}")
        return serial
    finally:
        system.disconnect()


def _print_layout(client, title: str) -> None:
    layout = client.read(LAYOUT_PATH).get_response(su.REST_COMMAND_TIMEOUT_MSEC).payload
    sensors = (layout.get("grid") or {}).get("sensors") or []
    print(f"\n{title}")
    print("*" * 32)
    for entry in sensors:
        print(f"Sensor ID: {entry.get('sensorId')}")
        print(f"Row: {entry.get('row')}, Column: {entry.get('column')}")
        print(f"Orientation: {entry.get('orientation')}")
        print(f"Multiplexing Bank: {entry.get('multiplexingBank')}\n")


def _resolve_additional_serials(add_ips: list[str], port: int) -> list[str]:
    if ADDITIONAL_SENSOR_SERIALS:
        return list(ADDITIONAL_SENSOR_SERIALS)
    return [_read_profiler_serial(ip, port) for ip in add_ips]


def _main(args: argparse.Namespace) -> int:
    from gopxl_sdk import GoSystem

    add_ips = args.add_ip if args.add_ip else list(ADDITIONAL_PROFILER_IPS)
    serials = _resolve_additional_serials(add_ips, args.port)

    system = GoSystem()
    if su.connect_system(system, args.master_ip, args.port):
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
        engine = client.read(PATHS.engine_path).get_response(su.REST_COMMAND_TIMEOUT_MSEC).payload
        embedded = (engine.get("_embedded") or {}).get("go:scanner")
        if not embedded:
            print("\nScanner not present, creating scanner...")
            client.create(SCANNERS_PATH).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        else:
            print("\nA sensor group already exists.")

        for serial in serials:
            print(f"\nAdding sensor {serial} to the sensor group...")
            client.create(SENSORS_PATH, {"serialNumber": serial}).check_response(
                su.REST_COMMAND_TIMEOUT_MSEC
            )

        _print_layout(client, "Current sensor layout:")

        layout = client.read(LAYOUT_PATH).get_response(su.REST_COMMAND_TIMEOUT_MSEC).payload
        sensors = (layout.get("grid") or {}).get("sensors") or []
        if len(sensors) > 1:
            print("Updating sensor layout...")
            layout["grid"]["sensors"][1]["row"] = 0
            layout["grid"]["sensors"][1]["column"] = 1
            layout["grid"]["sensors"][1]["orientation"] = 0
            client.update(LAYOUT_PATH, layout).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
            _print_layout(client, "Updated sensor layout:")

            remove_path = f"{SENSORS_PATH}/sensor-1"
            print(f"Removing {remove_path} from sensor group...")
            client.delete(remove_path).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        elif not serials:
            print("\nNo additional profilers configured. Set ADDITIONAL_PROFILER_IPS at the top of this file.")
    except Exception as exc:
        print(f"Layout update failed: {exc}")
        return su.ERROR_STATUS
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    su.bootstrap_sdk()
    from gopxl_sdk.exceptions import GoChannelError, GoRequestError

    parser = argparse.ArgumentParser(
        description="Configure multi-sensor layout across laser line profilers.",
    )
    parser.add_argument(
        "--master-ip",
        default=MASTER_SENSOR_IP,
        help="IP of the master profiler hosting the sensor group",
    )
    parser.add_argument(
        "--add-ip",
        action="append",
        default=None,
        metavar="IP",
        help="Additional profiler IP to add (repeat for each sensor)",
    )
    parser.add_argument("--port", type=int, default=CONTROL_PORT, help="Control port")
    args = parser.parse_args()

    try:
        return _main(args)
    except GoRequestError as exc:
        print(f"GoRequestError: {su.format_request_error(exc)}")
        print(f"Error sending a REST command to {getattr(exc, 'path', '')}")
        return su.ERROR_STATUS
    except GoChannelError as exc:
        print(f"Error: {exc}")
        print("Check sensor status, ensure it is connected, or try increasing timeout value.")
        return su.ERROR_STATUS
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return su.ERROR_STATUS


if __name__ == "__main__":
    raise SystemExit(main())
