"""
Acquire a 2D image from a SmartCam / 2dscanner device via GDP.

Designed for Gocator 1120-M and similar machine-vision cameras (engine id
``2dscanner``). Laser line profilers use receive_profile.py / receive_image.py
instead.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

IMAGE_TOOL_TYPE = "ImageFilter"
IMAGE_SOURCE = su.IMAGE_SOURCE_2D
SENSOR_2D_PATH = su.SENSOR_PATH_2D


def _work(system) -> None:
    from gopxl_sdk.enums import MessageType
    from gopxl_sdk.gdp_msg import GoGdpImage

    client = system.client()
    system.stop()

    print("\nSetting exposure...")
    client.update(
        SENSOR_2D_PATH,
        {"parameters": {"generalSettings": {"exposure": 10}}},
    ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)

    print("\nAdding ImageFilter tool...")
    client.create(
        su.TOOLS_PATH,
        {"type": IMAGE_TOOL_TYPE, "autoConnect": True, "position": 0},
    ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)

    print("\nEnabling Gocator Protocol...")
    gh.enable_gocator_protocol(system)
    if not gh.output_has_source(system, "image"):
        print(f"Adding GDP output: {IMAGE_SOURCE}")
        gh.add_gdp_output(system, IMAGE_SOURCE)

    print("\nConnecting to Gocator Protocol...")
    gdp = gh.connect_gdp(system)
    gh.start_if_ready(system)

    print("\nWaiting for an image dataset...")
    deadline = time.monotonic() + 10.0
    image_received = False
    while time.monotonic() < deadline and not image_received:
        gdp.receive_data_sync(su.RECEIVE_DATA_TIMEOUT_MSEC)
        for msg in gdp.dataset():
            if msg.type() == MessageType.IMAGE or isinstance(msg, GoGdpImage):
                image_received = True
                break
        if not image_received:
            print(".", end="", flush=True)

    print()
    if not image_received:
        print("No image data received within timeout.")
    else:
        print("A dataset with an Image message has been received.")
        gh.print_dataset_messages(gdp.dataset())

    gdp.close()
    system.stop()


def _main(args) -> int:
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    try:
        engine_id = su.resolve_engine_id(system, preferred=su.ENGINE_ID_2D)
        print(f"\nUsing scan engine: {engine_id}")
        if engine_id != su.ENGINE_ID_2D:
            print(
                "Warning: this sample targets 2dscanner (SmartCam / 1120-M). "
                f"Found '{engine_id}' instead — acquisition may fail."
            )
        _work(system)
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Acquire 2D image from a 2dscanner device.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
