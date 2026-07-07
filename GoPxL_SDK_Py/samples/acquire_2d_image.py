"""
Acquire a 2D image using software trigger and GDP.

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

SYSTEM_IP = "192.168.1.10"
CONTROL_PORT = 3600
ENGINE_ID = "2dscanner"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

PATHS = su.device_paths(ENGINE_ID, SCANNER_ID, SENSOR_ID)

# 1120-M / 2dscanner: software trigger source is 3 (0=Time, 3=Software).
SOFTWARE_TRIGGER_MODE = 3
TRIGGER_ACTION = f"{PATHS.scanner_path}/actions/trigger"


def _work(system) -> None:
    from gopxl_sdk.enums import GoSystemState, MessageType

    client = system.client()
    if system.running_state() == GoSystemState.RUNNING:
        system.stop()
    if not gh.is_replay_enabled(system):
        client.update(
            PATHS.sensor_path,
            {"parameters": {"triggerSettings": {"source": SOFTWARE_TRIGGER_MODE}}},
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    image_output = f"{PATHS.outputs_path}/image"
    source = client.read(image_output).get_response().payload.get("dataSourceId")
    gh.enable_gocator_protocol(system)
    if source:
        gh.ensure_gdp_output(system, str(source), "image")
    gdp = gh.connect_gdp(system)
    gh.start_if_ready(system)

    deadline = time.time() + 10
    dataset = gdp.dataset()
    while time.time() < deadline:
        client.call(TRIGGER_ACTION).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        gdp.receive_data_sync(su.RECEIVE_DATA_TIMEOUT_MSEC)
        dataset = gdp.dataset()
        if any(msg.type() == MessageType.IMAGE for msg in dataset):
            break

    gh.print_dataset_messages(dataset)
    gdp.close()
    system.stop()


def _main(args):
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    try:
        _work(system)
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Acquire 2D image with software trigger.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
