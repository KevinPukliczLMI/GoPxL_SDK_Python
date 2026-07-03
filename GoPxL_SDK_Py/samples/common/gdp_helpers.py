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


def output_has_source(system, source_key: str) -> bool:
    response = system.client().read(su.GOCATOR_OUTPUT_PATH).get_response(su.REST_COMMAND_TIMEOUT_MSEC)
    mapping = response.payload.get("map") or {}
    if isinstance(mapping, dict):
        items = mapping.values()
    elif isinstance(mapping, list):
        items = mapping
    else:
        items = []
    for item in items:
        if isinstance(item, dict) and source_key in str(item.get("source", "")):
            return True
    return False


def add_gdp_output(system, source_id: str, output_id: int = 0, auto_shift: bool = True) -> None:
    payload: dict[str, Any] = {
        "source": source_id,
        "outputId": output_id,
        "autoShift": auto_shift,
    }
    system.client().call(su.GOCATOR_ADD_OUTPUT_PATH, payload).check_response(su.REST_COMMAND_TIMEOUT_MSEC)


def ensure_scan_mode(system, mode: int) -> None:
    response = system.client().read(su.SCANNER_PATH).get_response(su.REST_COMMAND_TIMEOUT_MSEC)
    current = int(response.payload.get("parameters", {}).get("scanModeSettings", {}).get("scanMode", -1))
    if current != mode:
        payload = {"parameters": {"scanModeSettings": {"scanMode": mode}}}
        system.client().update(su.SCANNER_PATH, payload).check_response(su.REST_COMMAND_TIMEOUT_MSEC)


def connect_gdp(system):
    from gopxl_sdk import GoGdpClient

    client = GoGdpClient()
    client.connect(system.address(), system.gdp_port())
    return client


def start_if_ready(system) -> None:
    from gopxl_sdk.enums import GoSystemState

    if system.running_state() == GoSystemState.READY:
        print("\nStarting system...")
        system.start()


def setup_live_or_replay(system, scan_mode: int | None = None) -> bool:
    """Return True when replay is enabled; optionally set scan mode for live data."""
    replay = is_replay_enabled(system)
    if replay:
        print("\nUsing replay data")
        return True
    print("\nUsing live data")
    if scan_mode is not None:
        ensure_scan_mode(system, scan_mode)
    return False


def run_gdp_receive(system, source_id: str, source_key: str, timeout_ms: int | None = None) -> None:
    """Enable GDP, add output if needed, connect, start, and receive one dataset."""
    timeout = timeout_ms or su.RECEIVE_DATA_TIMEOUT_MSEC
    enable_gocator_protocol(system)
    if not output_has_source(system, source_key):
        add_gdp_output(system, source_id)
    print("\nConnecting to Gocator Protocol...")
    gdp = connect_gdp(system)
    start_if_ready(system)
    gdp.receive_data_sync(timeout)
    print_dataset_messages(gdp.dataset())
    gdp.close()
    system.stop()


def print_dataset_messages(dataset) -> None:
    from gopxl_sdk.gdp_msg import (
        GoGdpImage,
        GoGdpMeasurement,
        GoGdpNull,
        GoGdpProfilePointCloud,
        GoGdpProfileUniform,
        GoGdpStamp,
        GoGdpString,
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