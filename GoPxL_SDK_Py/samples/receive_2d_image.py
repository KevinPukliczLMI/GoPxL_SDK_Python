"""
Receive 2D camera images via GDP.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

IMAGE_OUTPUT_PATH = f"{su.OUTPUTS_PATH}/image"
TIME_TRIGGER_MODE = 0


def _work(system) -> None:
    client = system.client()
    if not gh.is_replay_enabled(system):
        client.update(
            su.SCANNER_PATH,
            {
                "parameters": {
                    "triggerSettings": {
                        "source": TIME_TRIGGER_MODE,
                        "frameRate": 10,
                        "maxFrameRateEnabled": False,
                    }
                }
            },
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    response = client.read(IMAGE_OUTPUT_PATH).get_response().payload
    source = response.get("dataSourceId")
    print(f"Image data source: {source}")
    gh.enable_gocator_protocol(system)
    if source and not gh.output_has_source(system, "image"):
        gh.add_gdp_output(system, source)
    gdp = gh.connect_gdp(system)
    gh.start_if_ready(system)
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
    return su.run_main("Receive 2D image via GDP.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
