"""
Receive uniform profile data via GDP.

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

def _work(system) -> None:
    gh.setup_live_or_replay(system, su.PROFILE_MODE)
    if not gh.is_replay_enabled(system):
        client = system.client()
        client.update(
            su.SCANNER_PATH,
            {"parameters": {"scanModeSettings": {"intensityEnabled": True}}},
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    gh.run_gdp_receive(system, su.profile_source_id(), "topUniformProfile")


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
    return su.run_main("Receive profile data via GDP.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
