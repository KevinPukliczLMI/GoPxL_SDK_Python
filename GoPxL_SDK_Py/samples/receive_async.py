"""
Receive GDP data asynchronously (e.g. measurements).

Does not modify sensor configuration — assumes Gocator Protocol and GDP outputs
are already enabled in the active job. Connects, listens on a callback, and exits.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

SYSTEM_IP = "192.168.1.10"
CONTROL_PORT = 3600


def _work(system) -> None:
    if gh.is_replay_enabled(system):
        print("\nUsing replay data")
    else:
        print("\nUsing live data")

    print("\nConnecting to Gocator Protocol...")
    gdp = gh.connect_gdp(system)

    received = threading.Event()

    def _on_data(dataset) -> None:
        gh.print_dataset_messages(dataset)
        received.set()

    print("\nRunning callback to receive data asynchronously...")
    gdp.receive_data_async(_on_data)
    if not received.wait(timeout=su.ASYNC_CALLBACK_TIMEOUT_SEC):
        from gopxl_sdk.exceptions import GoChannelError

        raise GoChannelError(
            f"Timeout after {su.ASYNC_CALLBACK_TIMEOUT_SEC}s waiting for async GDP data. "
            "Ensure GDP outputs are configured and the sensor is producing data."
        )
    gdp.close()


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
    return su.run_main("Receive GDP data asynchronously.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
