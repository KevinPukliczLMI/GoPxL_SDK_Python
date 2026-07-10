"""GDP setup helpers shared by receive samples."""

from __future__ import annotations

from typing import Any

from . import sample_utils as su


def is_replay_enabled(system) -> bool:
    response = system.client().read(su.REPLAY_PATH).get_response(su.REST_COMMAND_TIMEOUT_MSEC)
    return bool(response.payload.get("enabled"))


def enable_gocator_protocol(system) -> None:
    system.client().update(su.GOCATOR_CONTROL_PATH, {"enabled": True}).check_response(
        su.REST_COMMAND_TIMEOUT_MSEC
    )


GOCATOR_REMOVE_OUTPUT_PATH = "/controls/gocator/outputs/commands/remove"


def _normalize_source_id(source: str) -> str:
    value = source.strip()
    while len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1].strip()
    return value


def _gdp_output_items(system) -> list[dict[str, Any]]:
    response = system.client().read(su.GOCATOR_OUTPUT_PATH).get_response(su.REST_COMMAND_TIMEOUT_MSEC)
    mapping = response.payload.get("map") or {}
    if isinstance(mapping, dict):
        return [item for item in mapping.values() if isinstance(item, dict)]
    if isinstance(mapping, list):
        return [item for item in mapping if isinstance(item, dict)]
    return []


def _source_matches_source_key(source: str, source_key: str) -> bool:
    normalized = _normalize_source_id(source)
    if normalized == source_key:
        return True
    if ":" in source_key:
        return source_key in normalized
    return normalized.endswith(f":{source_key}")


def output_has_source(system, source_key: str) -> bool:
    for item in _gdp_output_items(system):
        if _source_matches_source_key(str(item.get("source", "")), source_key):
            return True
    return False


def add_gdp_output(system, source_id: str, output_id: int = 0, auto_shift: bool = True) -> None:
    payload: dict[str, Any] = {
        "source": _normalize_source_id(source_id),
        "outputId": output_id,
        "autoShift": auto_shift,
    }
    system.client().call(su.GOCATOR_ADD_OUTPUT_PATH, payload).check_response(su.REST_COMMAND_TIMEOUT_MSEC)


def _source_is_malformed(source: str) -> bool:
    return '"' in source


def ensure_gdp_output(system, source_id: str, source_key: str, output_id: int = 0) -> None:
    """Register a GDP output, replacing any existing entry with a malformed source."""
    normalized = _normalize_source_id(source_id)
    for item in _gdp_output_items(system):
        current_raw = str(item.get("source", ""))
        current = _normalize_source_id(current_raw)
        if not _source_matches_source_key(current_raw, source_key):
            continue
        if current == normalized and not _source_is_malformed(current_raw):
            return
        system.client().call(
            GOCATOR_REMOVE_OUTPUT_PATH,
            {"outputId": int(item.get("outputId", output_id))},
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    add_gdp_output(system, normalized, output_id=output_id)


def ensure_scan_mode(system, mode: int, scanner_path: str | None = None) -> None:
    path = scanner_path or su.SCANNER_PATH
    response = system.client().read(path).get_response(su.REST_COMMAND_TIMEOUT_MSEC)
    current = int(response.payload.get("parameters", {}).get("scanModeSettings", {}).get("scanMode", -1))
    if current != mode:
        payload = {"parameters": {"scanModeSettings": {"scanMode": mode}}}
        system.client().update(path, payload).check_response(su.REST_COMMAND_TIMEOUT_MSEC)


def connect_gdp(system):
    from GoPxL_SDK_Py import GoGdpClient

    client = GoGdpClient()
    client.connect(system.address(), system.gdp_port())
    return client


def start_if_ready(system) -> None:
    from GoPxL_SDK_Py.enums import GoSystemState

    if system.running_state() == GoSystemState.READY:
        print("\nStarting system...")
        system.start()


def setup_live_or_replay(system, scan_mode: int | None = None, scanner_path: str | None = None) -> bool:
    """Return True when replay is enabled; optionally set scan mode for live data."""
    replay = is_replay_enabled(system)
    if replay:
        print("\nUsing replay data")
        return True
    print("\nUsing live data")
    if scan_mode is not None:
        ensure_scan_mode(system, scan_mode, scanner_path)
    return False


def print_profile_messages(dataset) -> None:
    """Print only uniform/point-cloud profile messages (matches C++ ReceiveProfile)."""
    from GoPxL_SDK_Py.gdp_msg import GoGdpProfilePointCloud, GoGdpProfileUniform

    print(f"\nTotal number of messages: {dataset.count()}")
    profile_count = 0
    for index, msg in enumerate(dataset):
        if isinstance(msg, GoGdpProfileUniform):
            profile_count += 1
            print("\n" + "-" * 64)
            print(f"GDP Output Source {index + 1}")
            print("Message type: Uniform Profile")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data Source ID: {msg.data_source_id()}")
            valid = sum(1 for r in msg.ranges() if r != su.INT16_NULL)
            print(f"Profile points count: {msg.width()}")
            print(f"Valid points count: {valid}")
        elif isinstance(msg, GoGdpProfilePointCloud):
            profile_count += 1
            print("\n" + "-" * 64)
            print(f"GDP Output Source {index + 1}")
            print("Message type: Point Cloud Profile")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data Source ID: {msg.data_source_id()}")
            valid = sum(1 for x, z in msg.points() if x != su.INT16_NULL)
            print(f"Profile points count: {msg.width()}")
            print(f"Valid points count: {valid}")
    if profile_count == 0:
        print(
            "\nNo profile messages in this dataset. GDP delivers every configured output "
            "per frame; other messages (stamp, measurements, etc.) were received but not shown."
        )


def print_surface_messages(dataset) -> None:
    """Print only uniform/point-cloud surface messages (matches C++ ReceiveSurface)."""
    from GoPxL_SDK_Py.gdp_msg import GoGdpSurfacePointCloud, GoGdpSurfaceUniform

    print(f"\nTotal number of messages: {dataset.count()}")
    surface_count = 0
    for index, msg in enumerate(dataset):
        if isinstance(msg, GoGdpSurfaceUniform):
            surface_count += 1
            print("\n" + "-" * 64)
            print(f"GDP Output Source {index + 1}")
            print("Message type: Uniform Surface")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data Source ID: {msg.data_source_id()}")
            print(f"Length: {msg.length()}, Width: {msg.width()}")
            print(f"Range points: {len(msg.ranges())}")
            print(f"Intensity bytes: {len(msg.intensities())}")
        elif isinstance(msg, GoGdpSurfacePointCloud):
            surface_count += 1
            print("\n" + "-" * 64)
            print(f"GDP Output Source {index + 1}")
            print("Message type: Point Cloud Surface")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data Source ID: {msg.data_source_id()}")
            print(f"Length: {msg.length()}, Width: {msg.width()}")
            print(f"Range points: {len(msg.ranges())}")
            print(f"Intensity bytes: {len(msg.intensities())}")
    if surface_count == 0:
        print(
            "\nNo surface messages in this dataset. GDP delivers every configured output "
            "per frame; other messages (stamp, measurements, etc.) were received but not shown."
        )


def print_measurement_messages(dataset) -> None:
    """Print measurement/null messages with GDP and data-source IDs (matches C++ ReceiveMeasurement)."""
    from GoPxL_SDK_Py.gdp_msg import GoGdpMeasurement, GoGdpNull

    print(f"\nTotal number of messages: {dataset.count()}")
    for index, msg in enumerate(dataset):
        print("\n" + "-" * 64)
        print(f"GDP Output Source {index + 1}")
        if isinstance(msg, GoGdpMeasurement):
            print("Message type: Measurement")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data source ID: {msg.data_source_id()}")
            if msg.arrayed_count == 0:
                print("Not arrayed")
            else:
                print("Arrayed")
                print(f"\tCount: {msg.arrayed_count}")
                print(f"\tIndex: {msg.arrayed_index}")
            print(f"\tValue: {msg.value}")
            print(f"\tDecision: {msg.decision}")
        elif isinstance(msg, GoGdpNull):
            print("Message type: Null")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data source ID: {msg.data_source_id()}")
        else:
            print("No measurement found in the message.")


def print_dataset_messages(dataset) -> None:
    from GoPxL_SDK_Py.gdp_msg import (
        GoGdpImage,
        GoGdpMeasurement,
        GoGdpNull,
        GoGdpProfilePointCloud,
        GoGdpProfileUniform,
        GoGdpStamp,
        GoGdpString,
        GoGdpSurfacePointCloud,
        GoGdpSurfaceUniform,
    )

    print(f"\nTotal number of messages: {dataset.count()}")
    for index, msg in enumerate(dataset):
        print("\n" + "-" * 64)
        print(f"GDP Output Source {index + 1}")
        mtype = msg.type() if hasattr(msg, "type") else getattr(msg, "msg_type", None)
        if isinstance(msg, GoGdpProfileUniform):
            print("Message type: Uniform Profile")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data Source ID: {msg.data_source_id()}")
            valid = sum(1 for r in msg.ranges() if r != su.INT16_NULL)
            print(f"Profile points count: {msg.width()}")
            print(f"Valid points count: {valid}")
        elif isinstance(msg, GoGdpProfilePointCloud):
            print("Message type: Point Cloud Profile")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data Source ID: {msg.data_source_id()}")
            valid = sum(1 for x, z in msg.points() if x != su.INT16_NULL)
            print(f"Profile points count: {msg.width()}")
            print(f"Valid points count: {valid}")
        elif isinstance(msg, GoGdpImage):
            print("Message type: Image")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data Source ID: {msg.data_source_id()}")
            print(f"Width: {msg.width()}, Height: {msg.height()}")
            print(f"Row size: {msg.row_size()}, Pixel bytes: {len(msg.pixels())}")
            print(f"Pixel format: {msg.pixel_format}, Color filter: {msg.color_filter}")
            print(f"Flipped X/Y: {msg.flipped_x}/{msg.flipped_y}, Column based: {msg.column_based}")
        elif isinstance(msg, GoGdpSurfaceUniform):
            print("Message type: Uniform Surface")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data Source ID: {msg.data_source_id()}")
            print(f"Length: {msg.length()}, Width: {msg.width()}")
            print(f"Range points: {len(msg.ranges())}")
            print(f"Intensity bytes: {len(msg.intensities())}")
        elif isinstance(msg, GoGdpSurfacePointCloud):
            print("Message type: Point Cloud Surface")
            print(f"GDP ID: {msg.gdp_id}")
            print(f"Data Source ID: {msg.data_source_id()}")
            print(f"Length: {msg.length()}, Width: {msg.width()}")
            print(f"Range points: {len(msg.ranges())}")
            print(f"Intensity bytes: {len(msg.intensities())}")
        elif isinstance(msg, GoGdpStamp):
            print("Message type: Stamp")
            print(f"Frame index: {msg.frame_index}")
            print(f"Timestamp: {msg.timestamp}")
        elif isinstance(msg, GoGdpMeasurement):
            print("Message type: Measurement")
            print(f"Value: {msg.value}")
            print(f"Decision: {msg.decision}")
        elif isinstance(msg, GoGdpString):
            print("Message type: String")
            print(f"Text: {msg.text}")
            print(f"Decision: {msg.decision}")
        elif isinstance(msg, GoGdpNull):
            print("Message type: Null")
            print(f"Error status: {msg.error_status}")
        else:
            print(f"Message type: {mtype}")


def run_gdp_receive_configured(
    system,
    timeout_ms: int | None = None,
    *,
    print_fn=print_dataset_messages,
) -> None:
    """Enable GDP, connect, start, and receive one dataset without changing outputs."""
    timeout = timeout_ms or su.RECEIVE_DATA_TIMEOUT_MSEC
    enable_gocator_protocol(system)
    print("\nConnecting to Gocator Protocol...")
    gdp = connect_gdp(system)
    start_if_ready(system)
    gdp.receive_data_sync(timeout)
    print_fn(gdp.dataset())
    gdp.close()
    system.stop()


def run_gdp_receive(
    system,
    source_id: str,
    source_key: str,
    timeout_ms: int | None = None,
    *,
    print_fn=print_dataset_messages,
) -> None:
    """Enable GDP, add output if needed, connect, start, and receive one dataset."""
    timeout = timeout_ms or su.RECEIVE_DATA_TIMEOUT_MSEC
    enable_gocator_protocol(system)
    if not output_has_source(system, source_key):
        add_gdp_output(system, source_id)
    print("\nConnecting to Gocator Protocol...")
    gdp = connect_gdp(system)
    start_if_ready(system)
    gdp.receive_data_sync(timeout)
    print_fn(gdp.dataset())
    gdp.close()
    system.stop()