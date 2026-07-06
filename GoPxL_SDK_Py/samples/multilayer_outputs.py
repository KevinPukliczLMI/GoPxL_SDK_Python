"""
Receive multilayer profile array outputs via GDP.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

SYSTEM_IP = "192.168.1.10"
CONTROL_PORT = 3600

ARRAY_PROFILE_SOURCE = (
    f'"scan:{su.ENGINE_ID}:scanner-0:topUniformProfileArray"'
)
REMOVE_ALL_PATH = "/controls/gocator/outputs/commands/removeAll"


def _work(system) -> None:
    client = system.client()
    gh.setup_live_or_replay(system, su.PROFILE_MODE)
    try:
        client.call(REMOVE_ALL_PATH).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    except Exception:
        pass
    gh.enable_gocator_protocol(system)
    gh.add_gdp_output(system, ARRAY_PROFILE_SOURCE)
    gdp = gh.connect_gdp(system)
    gh.start_if_ready(system)
    gdp.receive_data_sync(su.RECEIVE_DATA_TIMEOUT_MSEC)
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
    return su.run_main("Receive multilayer GDP outputs.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
