"""
Save, rename, load, and download jobs.

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

JOB_NAME_0 = "SDK-demo"
JOB_NAME_1 = "SDK-demo-job"
JOB_NAME_2 = "SDK-local-job-demo"
SAVE_JOB_PATH = f"{su.JOBS_PATH}/commands/save"
RENAME_JOB_PATH = f"{su.JOBS_PATH}/commands/rename"
LOAD_JOB_PATH = f"{su.JOBS_PATH}/commands/load"


def _main(args):
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    client = system.client()
    try:
        response = client.read(su.JOB_FILES_PATH, args={"expandLevel": 1}).get_response().payload
        items = (response.get("_embedded") or {}).get("item") or []
        if items:
            print("\nList of saved jobs:")
            for item in items:
                print(item.get("jobName"))
        else:
            print("\nCurrently GoPxL does not contain any saved job.")

        client.call(SAVE_JOB_PATH, {"name": JOB_NAME_0}).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        try:
            client.call(
                RENAME_JOB_PATH,
                {"sourceName": JOB_NAME_0, "destName": JOB_NAME_1},
            ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        except Exception as exc:
            print(f"Rename failed: {exc}")

        data_path = f"{su.JOB_FILES_PATH}/{JOB_NAME_1}/data"
        job_data = client.read(data_path).get_response(su.RECEIVE_DATA_TIMEOUT_MSEC).payload
        content = job_data.get("content")
        if content is not None:
            local_path = Path(f"./{JOB_NAME_2}.job")
            local_path.write_bytes(bytes(content))
            print(f"Downloaded job to {local_path.resolve()}")

        client.call(LOAD_JOB_PATH, {"name": JOB_NAME_1}).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Manage jobs on the sensor.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
