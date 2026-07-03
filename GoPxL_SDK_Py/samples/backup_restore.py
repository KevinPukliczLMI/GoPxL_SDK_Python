"""
Backup and restore sensor configuration to a file.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import gdp_helpers as gh
from common import sample_utils as su

SYSTEM_BACKUP_PATH = "/system/commands/archive"
SYSTEM_RESTORE_PATH = "/system/commands/restore"
DEFAULT_BACKUP_FILE_PATH = Path("./sample_backup.gpbak")


def _main(args):
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    client = system.client()
    payload = {
        "contents": [
            "global",
            "allWorkspaces",
            "allJobs",
            "replay",
            "liveJob",
        ]
    }
    try:
        response = client.call(SYSTEM_BACKUP_PATH, payload).get_response(su.RECEIVE_DATA_TIMEOUT_MSEC)
        data = bytes(response.payload.get("data") or b"")
        DEFAULT_BACKUP_FILE_PATH.write_bytes(data)
        print(f"Backup saved to {DEFAULT_BACKUP_FILE_PATH.resolve()}")

        restore_payload = dict(payload)
        restore_payload["data"] = list(data)
        client.call(SYSTEM_RESTORE_PATH, restore_payload).check_response(
            su.REST_COMMAND_TIMEOUT_MSEC_EXTENDED
        )
        print("Restore command sent.")
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Backup and restore the sensor.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
