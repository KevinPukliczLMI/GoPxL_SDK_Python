"""
Acquire a 2D image using software trigger and GDP.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

SOFTWARE_TRIGGER_MODE = 3
TRIGGER_ACTION = f"{su.SCANNER_PATH}/actions/trigger"


def _work(system) -> None:
    client = system.client()
    client.update(
        su.SCANNER_PATH,
        {"parameters": {"triggerSettings": {"source": SOFTWARE_TRIGGER_MODE}}},
    ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    image_output = f"{su.OUTPUTS_PATH}/image"
    source = client.read(image_output).get_response().payload.get("dataSourceId")
    gh.enable_gocator_protocol(system)
    if source:
        gh.add_gdp_output(system, f'"{source}"')
    system.start()
    client.call(TRIGGER_ACTION).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    gdp = gh.connect_gdp(system)
    gdp.receive_data_sync(su.IMAGE_RECEIVE_TIMEOUT_MSEC)
    gh.print_dataset_messages(gdp.dataset())
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
    return su.run_main("Acquire 2D image with software trigger.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
