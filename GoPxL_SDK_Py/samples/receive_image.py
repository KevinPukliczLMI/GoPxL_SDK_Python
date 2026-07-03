"""
Receive heightmap image data via GDP.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

def _image_source() -> tuple[str, str]:
    key = "Image"
    source = f"scan:{su.ENGINE_ID}:{su.SCANNER_ID}:{su.SENSOR_ID}{key}0"
    return source, key


def _work(system) -> None:
    gh.setup_live_or_replay(system, su.SCAN_MODE_IMAGE)
    source_id, source_key = _image_source()
    gh.run_gdp_receive(system, source_id, source_key, su.IMAGE_RECEIVE_TIMEOUT_MSEC)


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
    return su.run_main("Receive image data via GDP.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
