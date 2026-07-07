"""
Backup and restore sensor configuration to a file.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.

Run backup (default):
    python backup_restore.py

Run restore from an existing .gpbak file:
    python backup_restore.py --restore
    python backup_restore.py --restore --file sample_backup.gpbak
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import sample_utils as su

SYSTEM_IP = "192.168.1.10"
CONTROL_PORT = 3600

SYSTEM_BACKUP_PATH = "/system/commands/archive"
SYSTEM_RESTORE_PATH = "/system/commands/restore"
DEFAULT_BACKUP_FILE_PATH = Path("./sample_backup.gpbak")

ARCHIVE_CONTENTS = {
    "contents": [
        "global",
        "allWorkspaces",
        "allJobs",
        "replay",
        "liveJob",
    ]
}


def _backup(system, backup_file: Path) -> None:
    client = system.client()
    print("\nReceiving backup data...")
    response = client.call(SYSTEM_BACKUP_PATH, ARCHIVE_CONTENTS).get_response(
        su.RECEIVE_DATA_TIMEOUT_MSEC
    )
    data = bytes(response.payload.get("data") or b"")
    backup_file.write_bytes(data)
    print(f"Backup saved to {backup_file.resolve()} ({len(data)} bytes)")


def _restore(system, backup_file: Path) -> None:
    if not backup_file.is_file():
        raise FileNotFoundError(
            f"Backup file not found: {backup_file.resolve()}\n"
            "Run with --backup first, or pass --file path/to/backup.gpbak"
        )
    client = system.client()
    data = backup_file.read_bytes()
    print(f"\nRestoring from {backup_file.resolve()} ({len(data)} bytes)...")
    restore_payload = dict(ARCHIVE_CONTENTS)
    restore_payload["data"] = list(data)
    client.call(SYSTEM_RESTORE_PATH, restore_payload).check_response(
        su.REST_COMMAND_TIMEOUT_MSEC_EXTENDED
    )
    print("Restore completed.")


def _main(args: argparse.Namespace) -> int:
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    try:
        if args.restore:
            _restore(system, args.file)
        else:
            _backup(system, args.file)
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    su.bootstrap_sdk()
    from gopxl_sdk.exceptions import GoChannelError, GoRequestError

    parser = argparse.ArgumentParser(description="Backup or restore sensor configuration.")
    parser.add_argument("--ip", default=SYSTEM_IP, help="Sensor IP address")
    parser.add_argument("--port", type=int, default=CONTROL_PORT, help="Control port")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_BACKUP_FILE_PATH,
        help="Backup file path (default: ./sample_backup.gpbak)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--backup",
        action="store_true",
        help="Archive sensor config to --file (default)",
    )
    mode.add_argument(
        "--restore",
        action="store_true",
        help="Restore sensor config from --file",
    )
    args = parser.parse_args()
    if not args.backup and not args.restore:
        args.backup = True

    try:
        return _main(args)
    except FileNotFoundError as exc:
        print(exc)
        return su.ERROR_STATUS
    except GoRequestError as exc:
        print(f"GoRequestError: {su.format_request_error(exc)}")
        print(f"Error sending a REST command to {getattr(exc, 'path', '')}")
        return su.ERROR_STATUS
    except GoChannelError as exc:
        print(f"Error: {exc}")
        print("Check sensor status, ensure it is connected, or try increasing timeout value.")
        return su.ERROR_STATUS
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return su.ERROR_STATUS


if __name__ == "__main__":
    raise SystemExit(main())
