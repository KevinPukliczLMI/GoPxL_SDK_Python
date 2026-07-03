"""
Receive image data via GDP.

- Laser profilers (LMILaserLineProfiler, etc.): heightmap image scan mode
- SmartCam / 1120-M (2dscanner): 2D camera image (same as receive_2d_image.py)

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


def _profiler_image_source(engine_id: str) -> tuple[str, str]:
    key = "Image"
    source = f"scan:{engine_id}:{su.SCANNER_ID}:{su.SENSOR_ID}{key}0"
    return source, key


def _work_profiler(system, engine_id: str) -> None:
    scanner_path = su.scanner_path_for(engine_id)
    print(f"\nLaser profiler heightmap image mode (engine={engine_id})")
    if not gh.is_replay_enabled(system):
        print("\nSetting scan mode to Image...")
        system.client().update(
            scanner_path,
            {"parameters": {"scanModeSettings": {"scanMode": su.SCAN_MODE_IMAGE}}},
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    source_id, source_key = _profiler_image_source(engine_id)
    gh.run_gdp_receive(system, source_id, source_key, su.IMAGE_RECEIVE_TIMEOUT_MSEC)


def _work_2d_camera(system) -> None:
    client = system.client()
    print("\n2D camera image mode (engine=2dscanner)")
    print("(For dedicated SmartCam flow see also receive_2d_image.py / acquire_2d_image.py)")
    system.stop()

    if not gh.is_replay_enabled(system):
        print("\nConfiguring time trigger...")
        client.update(
            su.SENSOR_PATH_2D,
            {"/parameters/triggerSettings/source": TIME_TRIGGER_MODE},
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)

    image_output = f"{su.OUTPUTS_PATH_2D}/image"
    try:
        response = client.read(image_output).get_response().payload
        source = response.get("dataSourceId") or su.IMAGE_SOURCE_2D
    except Exception:
        source = su.IMAGE_SOURCE_2D
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
        engine_id = su.resolve_engine_id(system)
        print(f"\nUsing scan engine: {engine_id}")
        if engine_id == su.ENGINE_ID_2D:
            _work_2d_camera(system)
        else:
            _work_profiler(system, engine_id)
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Receive image data via GDP.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
