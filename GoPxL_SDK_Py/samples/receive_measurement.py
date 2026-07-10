"""
Receive tool measurement output via GDP.

Assumes measurement outputs are already enabled and listed under
/controls/gocator/outputs (see configure_tool.py). GDP ID on each message
matches GoPxL outputId; data source ID matches the output source string.

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

# Optional: set to a tool output source from GoPxL (e.g. tools:ProfilePartDetection-0:outputs:Height).
# Leave empty to use whatever is already in the job's GDP output map (C++ default).
MEASUREMENT_SOURCE = ""


def _work(system) -> None:
    gh.setup_live_or_replay(system)
    if MEASUREMENT_SOURCE:
        gh.run_gdp_receive(
            system,
            MEASUREMENT_SOURCE,
            MEASUREMENT_SOURCE,
            print_fn=gh.print_measurement_messages,
        )
    else:
        gh.run_gdp_receive_configured(system, print_fn=gh.print_measurement_messages)


def _main(args):
    from GoPxL_SDK_Py import GoSystem

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
    return su.run_main("Receive measurement data via GDP.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
