"""Common utilities and constants for GoPxL Python samples."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

# Engine and device identification (Gocator laser profiler defaults).
ENGINE_ID = "LMILaserLineProfiler"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

API_VERSION_PATH = "/version"
ENVIRON_INFO_PATH = "/environ/info"
REMOTE_CONTROLLER_PATH = "/environ/remoteController"
VISIBLE_SENSORS_PATH = "/scan/visibleSensors/"
IP_CONFIG_PATH = "/environ/ipConfig"

ENGINE_PATH = f"/scan/engines/{ENGINE_ID}"
SCANNER_PATH = f"{ENGINE_PATH}/scanners/{SCANNER_ID}"
SENSORS_PATH = f"{SCANNER_PATH}/sensors"
SENSOR_PATH = f"{SCANNER_PATH}/sensors/{SENSOR_ID}"
SCAN_MODE_PATH = "/parameters/scanModeSettings/scanMode"
OUTPUTS_PATH = f"{SCANNER_PATH}/outputs"

GOCATOR_CONTROL_PATH = "/controls/gocator"
GOCATOR_OUTPUT_PATH = "/controls/gocator/outputs"
GOCATOR_ADD_OUTPUT_PATH = "/controls/gocator/outputs/commands/add"
REPLAY_PATH = "/replay/playback"
DIGITAL_OUTPUT_PATH = "/controls/digitalOutput"

JOBS_PATH = "/jobs"
JOB_FILES_PATH = "/jobs/files"

ERROR_STATUS = 1
OK_STATUS = 0

REST_COMMAND_TIMEOUT_MSEC = 3000
REST_COMMAND_TIMEOUT_MSEC_EXTENDED = 30000
DISCOVER_TIMEOUT_MSEC = 3000
RECEIVE_DATA_TIMEOUT_MSEC = 20000
IMAGE_RECEIVE_TIMEOUT_MSEC = 60000
ASYNC_CALLBACK_TIMEOUT_SEC = 3

SCAN_MODE_IMAGE = 0
SCAN_MODE_PROFILE = 2
PROFILE_MODE = 2
SURFACE_MODE = 3

TOOLS_PATH = "/tools/"
DATA_SOURCES_PATH = "/dataSources/"
TOOL_TYPE = "ProfileBoundingBox"
TOOL_ID = "ProfileBoundingBox-demo"
TOOL_PATH = f"{TOOLS_PATH}extId={TOOL_ID}"
TOOL_INPUTS_PATH = f"{TOOL_PATH}/inputs"
PROFILE_INPUT_PATH = f"{TOOL_INPUTS_PATH}/ProfileInput"
TOOL_OUTPUT_NAME = "X"
TOOL_OUTPUT_PATH = f"{TOOL_PATH}/outputs/{TOOL_OUTPUT_NAME}"
METRICS_PATH = f"{TOOL_PATH}/metrics"
TOOL_OUTPUT_DATA_PATH = f"tools:{TOOL_TYPE}-0:outputs:{TOOL_OUTPUT_NAME}"
TOP_UNIFORM_PROFILE = f"scan:{ENGINE_ID}:scanner-0:topUniformProfile"

DEFAULT_SYSTEM_IP = "192.168.1.10"
DEFAULT_CONTROL_PORT = 3600

APPLICATION_TYPES = {
    0: "Gocator Sensor",
    1: "GoPxL on PC",
    2: "GoMax",
    3: "GoPxL Daemon",
}

HMI_STATUS = {
    0: "RUNNING",
    1: "STOPPED",
    2: "STARTING",
    3: "STOPPING",
    4: "FAILED_TO_START",
    5: "FAILED_TO_STOP",
}

INT16_NULL = -32768


def bootstrap_sdk() -> None:
    if "gopxl_sdk" in sys.modules:
        return
    sdk_root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "gopxl_sdk",
        sdk_root / "__init__.py",
        submodule_search_locations=[str(sdk_root)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load gopxl_sdk from {sdk_root}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["gopxl_sdk"] = module
    spec.loader.exec_module(module)


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--ip", default=DEFAULT_SYSTEM_IP, help="Sensor IP address")
    parser.add_argument("--port", type=int, default=DEFAULT_CONTROL_PORT, help="Control port")
    return parser.parse_args()


def print_section(header: str) -> None:
    print()
    print("=" * 81)
    print(header)
    print("=" * 81)
    print()


def format_request_error(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    if response is None:
        return str(exc)
    payload = getattr(response, "payload", {}) or {}
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            return f"{first.get('status', '')} - {first.get('description', '')}"
    return str(exc)


def verify_connection(system) -> int:
    from gopxl_sdk.exceptions import GoRequestError

    client = system.client()
    try:
        version = client.read(API_VERSION_PATH).get_response(REST_COMMAND_TIMEOUT_MSEC).payload
        print(f"\nAPI version is {version.get('apiVersion', version)}.")
    except GoRequestError as exc:
        print(f"Error: {format_request_error(exc)}")
        print("Failed to read API version. Check API path.")
        return ERROR_STATUS

    try:
        info = client.read(ENVIRON_INFO_PATH).get_response(REST_COMMAND_TIMEOUT_MSEC).payload
        app_type = int(info.get("applicationType", -1))
        serial = info.get("serialNumber", "")
        model = info.get("model", "")
        label = APPLICATION_TYPES.get(app_type, f"Unknown ({app_type})")
        if app_type == 0:
            print(f"\nThis device is a {label} model {model} with serial number {serial}.")
        elif app_type in (1, 3):
            print(f"\nThis device is a {label}.")
        else:
            print(f"\nThis device is a {label} model {model} with serial number {serial}.")
        if app_type != 0:
            sensor = client.read(SENSOR_PATH).get_response(REST_COMMAND_TIMEOUT_MSEC).payload
            print(
                f"The serial number of {SCANNER_ID} {SENSOR_ID} is {sensor.get('serialNumber', '')}."
            )
    except GoRequestError as exc:
        print(f"Error: {format_request_error(exc)}")
        print("Failed to read environment information. Check API path.")
        return ERROR_STATUS

    try:
        remote = client.read(REMOTE_CONTROLLER_PATH).get_response(REST_COMMAND_TIMEOUT_MSEC).payload
        if remote.get("remoteConnected"):
            print(
                f"\nThis device is controlled by a remote controller at IP {remote.get('ipAddress')} "
                f"with control port {remote.get('controlPort')}."
            )
            print("Please use the IP address of the remote controller (previously called accelerator).")
            return ERROR_STATUS
    except GoRequestError as exc:
        print(f"Error: {format_request_error(exc)}")
        print("Failed to read remote controller information. Check API path.")
        return ERROR_STATUS

    return OK_STATUS


def connect_system(system, ip: str, port: int) -> int:
    from gopxl_sdk.exceptions import GoChannelError, GoRequestError

    system.set_address(ip)
    system.set_control_port(port)
    print(f"\nConnecting to {ip}:{port}...")
    try:
        system.connect()
    except (GoRequestError, GoChannelError) as exc:
        print(f"Error: {exc}")
        print("Connection failed. Check if sensor is powered on, connected, and using correct IP/port.")
        return ERROR_STATUS
    return OK_STATUS


def profile_source_id(engine_id: str = ENGINE_ID) -> str:
    layer = "Layer0" if engine_id == "LMIConfocalLineProfiler" else ""
    key = "topUniformProfile" + layer
    return f"scan:{engine_id}:scanner-0:{key}"


def surface_source_id(engine_id: str = ENGINE_ID, scanner_id: str = SCANNER_ID) -> str:
    component = SENSOR_ID if engine_id == "LMIFringeSnapshot" else "top"
    layer = "Layer0" if engine_id == "LMIConfocalLineProfiler" else ""
    key = f"{component}UniformSurface{layer}"
    return f"scan:{engine_id}:{scanner_id}:{key}"


def stamp_source_id(engine_id: str = ENGINE_ID) -> str:
    return f"scan:{engine_id}:scanner-0:stamp"


def run_main(description: str, runner) -> int:
    bootstrap_sdk()
    from gopxl_sdk.exceptions import GoChannelError, GoRequestError

    args = parse_args(description)
    try:
        return runner(args)
    except GoRequestError as exc:
        print(f"GoRequestError: {format_request_error(exc)}")
        print(f"Error sending a REST command to {getattr(exc, 'path', '')}")
        return ERROR_STATUS
    except GoChannelError as exc:
        print(f"Error: {exc}")
        print("Check sensor status, ensure it is connected, or try increasing timeout value.")
        return ERROR_STATUS
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return ERROR_STATUS