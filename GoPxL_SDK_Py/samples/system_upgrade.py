"""
Upload a firmware package and monitor upgrade state.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

UPGRADE_COMMAND = "/system/commands/upgrade"
UPGRADE_ARCHIVE_PATH = Path("./upgrade_archive.dat")


def _main(args):
    from gopxl_sdk import GoSystem
    import time

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    if not UPGRADE_ARCHIVE_PATH.is_file():
        print(f"Upgrade archive not found: {UPGRADE_ARCHIVE_PATH.resolve()}")
        print("Place upgrade_archive.dat next to the sample before running.")
        system.disconnect()
        return su.ERROR_STATUS
    package = list(UPGRADE_ARCHIVE_PATH.read_bytes())
    client = system.client()
    try:
        client.call(UPGRADE_COMMAND, {"package": package}).check_response(60_000)
        deadline = time.time() + 300
        while time.time() < deadline:
            state = int(client.read("/system").get_response().payload.get("upgradeState", 0))
            print(f"upgradeState: {state}")
            if state in (0, -1):
                break
            time.sleep(2)
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Upgrade sensor firmware from a local archive.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
