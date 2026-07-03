"""
List commands/actions and invoke scanner actions via GoResource.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common import gdp_helpers as gh
from common import sample_utils as su

def _main(args):
    from gopxl_sdk import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    try:
        scanner = system.resource(su.SCANNER_PATH)
        jobs = system.resource(su.JOBS_PATH)

        print("Scanner commands:")
        for name in scanner.command_names():
            print(f"  {name}")
        print("Scanner actions:")
        for name in scanner.action_names():
            print(f"  {name}")

        jobs.call_command("save", {"name": "SDK_resource_api_demo"})
        print("Job saved via call_command('save').")

        system.start()
        scanner.call_action("trigger")
        print("Software trigger sent via call_action('trigger').")
        system.stop()

        job_files = system.resource(su.JOB_FILES_PATH)
        job_files.set_expand_level(1)
        children = job_files.children()
        print(f"Saved jobs ({len(children)}):")
        for child in children:
            print(f"  {child.get_string('/jobName')} ({child.uri()})")
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("GoResource commands and actions sample.", _main)


if __name__ == "__main__":
    raise SystemExit(main())
