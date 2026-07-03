"""
Run scanner alignment and read calibration transform.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

ALIGN_COMMAND_PATH = f"{su.SCANNER_PATH}/commands/align"
CLEAR_ALIGN_COMMAND_PATH = f"{su.SCANNER_PATH}/commands/clearAlign"
ALIGNMENT_STATE_PATH = f"{su.SCANNER_PATH}/alignment"
CALIBRATION_PATH = f"{su.SENSOR_PATH}/transform"
ALIGNING_STATUS = 2


def _main(args):
    from gopxl_sdk import GoSystem
    import time

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    client = system.client()
    try:
        client.call(f"{su.JOBS_PATH}/commands/save", {"name": "SDK_alignment_sample"}).check_response(
            su.REST_COMMAND_TIMEOUT_MSEC
        )
        client.call(CLEAR_ALIGN_COMMAND_PATH).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        client.call(ALIGN_COMMAND_PATH).check_response(su.REST_COMMAND_TIMEOUT_MSEC_EXTENDED)
        align_state = ALIGNING_STATUS
        while align_state == ALIGNING_STATUS:
            time.sleep(1)
            align_state = int(
                client.read(ALIGNMENT_STATE_PATH).get_response().payload.get("alignState", 0)
            )
        print(f"Alignment state: {align_state}")
        transform = client.read(CALIBRATION_PATH).get_response().payload
        print(f"Alignment transform: {transform}")
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Align the sensor.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
