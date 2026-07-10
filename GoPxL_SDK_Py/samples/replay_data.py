"""
Record, replay, and seek recorded scan data.

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
ENGINE_ID = "LMILaserLineProfiler"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

PATHS = su.device_paths(ENGINE_ID, SCANNER_ID, SENSOR_ID)

RECORDING_PATH = "/replay/recording"
REPLAY_SEEK_PATH = "/replay/commands/seek"
TIME_TRIGGER_MODE = 0


def _main(args):
    from GoPxL_SDK_Py import GoSystem

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    client = system.client()
    try:
        client.update(RECORDING_PATH, {"enabled": True}).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        client.update(
            PATHS.scanner_path,
            {
                "parameters": {
                    "triggerSettings": {
                        "source": TIME_TRIGGER_MODE,
                        "maxFrameRateEnabled": False,
                        "frameRate": 10,
                    }
                }
            },
        ).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        gh.start_if_ready(system)
        print("Recording live data (waiting 3 seconds)...")
        import time

        time.sleep(3)
        system.stop()
        client.update(su.REPLAY_PATH, {"enabled": True}).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        client.call(REPLAY_SEEK_PATH, {"index": 0}).check_response(su.REST_COMMAND_TIMEOUT_MSEC)
        gh.run_gdp_receive(system, su.profile_source_id(ENGINE_ID), "topUniformProfile")
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("Record and replay sensor data.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
