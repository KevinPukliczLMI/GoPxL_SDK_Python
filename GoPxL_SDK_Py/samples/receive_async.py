"""
Receive stamp data asynchronously via GDP.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

import threading
import time


def _on_data(dataset) -> None:
    gh.print_dataset_messages(dataset)


def _work(system) -> None:
    gh.setup_live_or_replay(system)
    gh.enable_gocator_protocol(system)
    gh.add_gdp_output(system, su.stamp_source_id())
    gdp = gh.connect_gdp(system)
    gh.start_if_ready(system)
    gdp.receive_data_async(_on_data)
    time.sleep(su.ASYNC_CALLBACK_TIMEOUT_SEC)
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
    return su.run_main("Receive GDP data asynchronously.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
