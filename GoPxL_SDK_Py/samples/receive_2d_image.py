"""
Receive 2D camera images via GDP.

Designed for Gocator 1120-M and similar machine-vision cameras (engine id
``2dscanner``). Laser line profilers use receive_profile.py / receive_image.py
instead.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

TIME_TRIGGER_MODE = 0
IMAGE_SOURCE = su.IMAGE_SOURCE_2D
SENSOR_2D_PATH = su.SENSOR_PATH_2D


def _work(system) -> None:
    client = system.client()
    system.stop()

    if not gh.is_replay_enabled(system):
        # Match C++ Receive2dImage: only set trigger source (do not force frameRate —
        # sensors reject values above their maximum).
        print("\nConfiguring time trigger...")
        client.update(
            SENSOR_2D_PATH,
            {"/parameters/triggerSettings/source": TIME_TRIGGER_MODE},
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)

    image_output = f"{su.OUTPUTS_PATH_2D}/image"
    try:
        response = client.read(image_output).get_response().payload
        source = response.get("dataSourceId") or IMAGE_SOURCE
    except Exception:
        source = IMAGE_SOURCE
    print(f"Image data source: {source}")

    gh.enable_gocator_protocol(system)
    if not gh.output_has_source(system, "image"):
        gh.add_gdp_output(system, source)

    print("\nConnecting to Gocator Protocol...")
    gdp = gh.connect_gdp(system)
    gh.start_if_ready(system)
    gdp.receive_data_sync(su.IMAGE_RECEIVE_TIMEOUT_MSEC)
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
    return su.run_main("Receive 2D image via GDP.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
