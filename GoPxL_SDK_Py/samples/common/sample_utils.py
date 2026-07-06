"""Common utilities and constants for GoPxL Python samples."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Engine and device identification (Gocator laser profiler defaults).
ENGINE_ID = "LMILaserLineProfiler"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

# 2D / SmartCam engine (Gocator 1120-M and similar machine-vision cameras).
ENGINE_ID_2D = "2dscanner"
ENGINE_PATH_2D = f"/scan/engines/{ENGINE_ID_2D}"
SCANNER_PATH_2D = f"{ENGINE_PATH_2D}/scanners/{SCANNER_ID}"
SENSOR_PATH_2D = f"{SCANNER_PATH_2D}/sensors/{SENSOR_ID}"
OUTPUTS_PATH_2D = f"{SCANNER_PATH_2D}/outputs"
IMAGE_SOURCE_2D = f"scan:{ENGINE_ID_2D}:{SCANNER_ID}:image"

API_VERSION_PATH = "/version"
ENVIRON_INFO_PATH = "/environ/info"
REMOTE_CONTROLLER_PATH = "/environ/remoteController"
VISIBLE_SENSORS_PATH = "/scan/visibleSensors/"
IP_CONFIG_PATH = "/environ/ipConfig"
ENGINES_PATH = "/scan/engines"

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


@dataclass(frozen=True, slots=True)
class DevicePaths:
    engine_id: str
    scanner_id: str
    sensor_id: str
    engine_path: str
    scanner_path: str
    sensor_path: str
    outputs_path: str
    sensors_path: str


def device_paths(
    engine_id: str,
    scanner_id: str = SCANNER_ID,
    sensor_id: str = SENSOR_ID,
) -> DevicePaths:
    """Build REST paths for a scan engine. Set engine_id at the top of each sample."""
    scanner_path = f"/scan/engines/{engine_id}/scanners/{scanner_id}"
    return DevicePaths(
        engine_id=engine_id,
        scanner_id=scanner_id,
        sensor_id=sensor_id,
        engine_path=f"/scan/engines/{engine_id}",
        scanner_path=scanner_path,
        sensor_path=f"{scanner_path}/sensors/{sensor_id}",
        outputs_path=f"{scanner_path}/outputs",
        sensors_path=f"{scanner_path}/sensors",
    )


def bootstrap_sdk() -> None:
    """Load gopxl_sdk from pip install, or from the parent repo when developing locally."""
    if "gopxl_sdk" in sys.modules:
        return
    try:
        import gopxl_sdk  # noqa: F401
        return
    except ImportError:
        pass
    sdk_root = Path(__file__).resolve().parents[2]
    init_py = sdk_root / "__init__.py"
    if not init_py.is_file():
        raise ImportError(
            "gopxl_sdk is not installed. Run:\n"
            "  pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git"
        )
    spec = importlib.util.spec_from_file_location(
        "gopxl_sdk",
        init_py,
        submodule_search_locations=[str(sdk_root)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "gopxl_sdk is not installed. Run: "
            "pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["gopxl_sdk"] = module
    spec.loader.exec_module(module)


def parse_args(
    description: str,
    *,
    default_ip: str,
    default_port: int = DEFAULT_CONTROL_PORT,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--ip", default=default_ip, help="Sensor IP address")
    parser.add_argument("--port", type=int, default=default_port, help="Control port")
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


def _engine_ids_from_payload(payload: dict) -> list[str]:
    """Extract engine ids from an engines collection payload."""
    engine_ids: list[str] = []
    embedded = payload.get("_embedded") or {}
    for key in ("item", "go:engine", "engines"):
        items = embedded.get(key)
        if items is None:
            continue
        if isinstance(items, dict):
            items = [items]
        for item in items:
            if not isinstance(item, dict):
                continue
            href = ((item.get("_links") or {}).get("self") or {}).get("href", "")
            engine_id = str(href).rstrip("/").split("/")[-1]
            if not engine_id or engine_id in ("engines", "scan"):
                engine_id = str(item.get("id") or item.get("engineId") or "")
            if engine_id and engine_id not in engine_ids:
                engine_ids.append(engine_id)
    # Some responses list engines as a top-level map/list.
    for key in ("engines", "items"):
        items = payload.get(key)
        if isinstance(items, dict):
            for engine_id in items:
                if engine_id and engine_id not in engine_ids:
                    engine_ids.append(str(engine_id))
        elif isinstance(items, list):
            for item in items:
                if isinstance(item, str) and item not in engine_ids:
                    engine_ids.append(item)
                elif isinstance(item, dict):
                    engine_id = str(item.get("id") or item.get("engineId") or "")
                    if engine_id and engine_id not in engine_ids:
                        engine_ids.append(engine_id)
    return engine_ids


def _engine_is_live(system, engine_id: str) -> bool:
    """True if the engine's default scanner path exists on the device."""
    from gopxl_sdk.exceptions import GoRequestError

    try:
        system.client().read(scanner_path_for(engine_id)).get_response(REST_COMMAND_TIMEOUT_MSEC)
        return True
    except GoRequestError:
        return False


def resolve_engine_id(system, preferred: str | None = None) -> str:
    """Return a live scan engine id (one whose scanner path exists)."""
    candidates: list[str] = []
    try:
        payload = system.client().read(ENGINES_PATH, args={"expandLevel": 1}).get_response(
            REST_COMMAND_TIMEOUT_MSEC
        ).payload
        candidates.extend(_engine_ids_from_payload(payload))
    except Exception:
        pass

    # Visible sensors often report the active engine even when /engines is sparse.
    try:
        sensors = (
            system.client()
            .read(VISIBLE_SENSORS_PATH, args={"expandLevel": 1})
            .get_response(REST_COMMAND_TIMEOUT_MSEC)
            .payload.get("sensors")
            or []
        )
        for sensor in sensors:
            if not isinstance(sensor, dict):
                continue
            engine_id = str(sensor.get("engineId") or "")
            if engine_id and engine_id not in candidates:
                candidates.append(engine_id)
            path = str(sensor.get("path") or "")
            # path like /scan/engines/2dscanner/scanners/scanner-0/sensors/sensor-0
            parts = path.strip("/").split("/")
            if len(parts) >= 3 and parts[0] == "scan" and parts[1] == "engines":
                engine_id = parts[2]
                if engine_id and engine_id not in candidates:
                    candidates.append(engine_id)
    except Exception:
        pass

    for engine_id in (preferred, ENGINE_ID_2D, ENGINE_ID, "LMIConfocalLineProfiler", "LMIFringeSnapshot"):
        if engine_id and engine_id not in candidates:
            candidates.append(engine_id)

    live = [engine_id for engine_id in candidates if _engine_is_live(system, engine_id)]
    if preferred and preferred in live:
        return preferred
    if live:
        return live[0]
    raise RuntimeError(
        "No live scan engines found on device. "
        f"Candidates checked: {', '.join(candidates) or '(none)'}"
    )


def scanner_path_for(engine_id: str) -> str:
    return f"/scan/engines/{engine_id}/scanners/{SCANNER_ID}"


def sensor_path_for(engine_id: str) -> str:
    return f"{scanner_path_for(engine_id)}/sensors/{SENSOR_ID}"


def outputs_path_for(engine_id: str) -> str:
    return f"{scanner_path_for(engine_id)}/outputs"


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


def run_main(
    description: str,
    runner,
    *,
    default_ip: str,
    default_port: int = DEFAULT_CONTROL_PORT,
) -> int:
    bootstrap_sdk()
    from gopxl_sdk.exceptions import GoChannelError, GoRequestError

    args = parse_args(description, default_ip=default_ip, default_port=default_port)
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