"""
Receive single and multi-layer profile outputs via GDP.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.

Requires a Gocator Confocal Profiler (G4 or G5 family) with engine
LMIConfocalLineProfiler and uniform spacing enabled. Not supported on laser
line profilers (LMILaserLineProfiler).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

# Gocator Confocal Profiler (G4 / G5) — not laser line profiler.
SYSTEM_IP = "192.168.1.40"
CONTROL_PORT = 3600
ENGINE_ID = "LMIConfocalLineProfiler"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

PATHS = su.device_paths(ENGINE_ID, SCANNER_ID, SENSOR_ID)

SENSOR_POSITION = "top"
ARRAY_PROFILE_SOURCE = f"scan:{ENGINE_ID}:{SCANNER_ID}:{SENSOR_POSITION}UniformProfileArray"
REMOVE_ALL_PATH = "/controls/gocator/outputs/commands/removeAll"
LAYER_COUNT_MULTI = 8


def _layer_source(layer: int) -> str:
    return f"scan:{ENGINE_ID}:{SCANNER_ID}:{SENSOR_POSITION}UniformProfileLayer{layer}"


def _setup_confocal_scanner(system, client) -> None:
    gh.ensure_scan_mode(system, su.PROFILE_MODE, PATHS.scanner_path)
    print("\nEnabling uniform spacing...")
    client.update(
        PATHS.scanner_path,
        {
            "parameters": {
                "scanModeSettings": {
                    "uniformSpacingEnabled": True,
                    "individualLayersEnabled": False,
                }
            }
        },
    ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)


def _set_layer_count(client, count: int) -> None:
    client.update(
        PATHS.sensor_path,
        {"parameters": {"layerSettings": {"layerCount": count}}},
    ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)


def _clear_gdp_outputs(client) -> None:
    try:
        client.call(REMOVE_ALL_PATH).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    except Exception:
        pass


def _receive_once(system, gdp, title: str) -> None:
    su.print_section(title)
    gh.start_if_ready(system)
    gdp.receive_data_sync(su.RECEIVE_DATA_TIMEOUT_MSEC)
    gh.print_dataset_messages(gdp.dataset())
    system.stop()


def _work(system) -> int:
    if ENGINE_ID != "LMIConfocalLineProfiler":
        print(
            "This sample requires a Gocator Confocal Profiler (G4/G5) "
            f"with engine LMIConfocalLineProfiler, not {ENGINE_ID}."
        )
        return su.ERROR_STATUS

    client = system.client()
    _setup_confocal_scanner(system, client)
    gh.enable_gocator_protocol(system)
    gdp = gh.connect_gdp(system)

    # Phase 1: single-layer profile array output
    _set_layer_count(client, 1)
    _clear_gdp_outputs(client)
    gh.add_gdp_output(system, ARRAY_PROFILE_SOURCE)
    _receive_once(system, gdp, "Single-layer profile array output")

    # Phase 2: multi-layer profile array output (8 layers)
    _clear_gdp_outputs(client)
    _set_layer_count(client, LAYER_COUNT_MULTI)
    gh.add_gdp_output(system, ARRAY_PROFILE_SOURCE)
    _receive_once(system, gdp, f"Multi-layer profile array output ({LAYER_COUNT_MULTI} layers)")

    # Phase 3: separated per-layer GDP outputs
    _clear_gdp_outputs(client)
    print("\nEnabling individual layer outputs...")
    client.update(
        PATHS.scanner_path,
        {"parameters": {"scanModeSettings": {"individualLayersEnabled": True}}},
    ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    for layer in range(LAYER_COUNT_MULTI):
        print(f"Adding profile layer {layer} to GDP output...")
        gh.add_gdp_output(system, _layer_source(layer))
    _receive_once(system, gdp, "Separated multi-layer profile outputs")

    gdp.close()
    return su.OK_STATUS


def _main(args):
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    try:
        return _work(system)
    finally:
        system.disconnect()


def main() -> int:
    return su.run_main(
        "Receive multilayer GDP outputs from a Gocator Confocal Profiler (G4/G5).",
        _main,
        default_ip=SYSTEM_IP,
        default_port=CONTROL_PORT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
