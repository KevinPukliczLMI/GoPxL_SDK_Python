"""
Inspect JSON schemas and validate values with GoResource.

GoPxL Python SDK sample - port of the C++ sample.
Copyright (C) 2022-2026 by LMI Technologies Inc. Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common import gdp_helpers as gh
from common import sample_utils as su

SYSTEM_IP = "192.168.1.10"
CONTROL_PORT = 3600
ENGINE_ID = "2dscanner"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

PATHS = su.device_paths(ENGINE_ID, SCANNER_ID, SENSOR_ID)ENGINE_ID = "2dscanner"
SCANNER_ID = "scanner-0"
SENSOR_ID = "sensor-0"

PATHS = su.device_paths(ENGINE_ID, SCANNER_ID, SENSOR_ID)
def _print_schema(label: str, schema: dict) -> None:
    print(f"{label}:")
    for key in ("type", "readOnly", "minimum", "maximum", "enum", "enumText", "units", "title"):
        if key in schema:
            print(f"  {key}: {schema[key]}")


def _main(args):
    from GoPxL_SDK_Py import GoSystem
    from GoPxL_SDK_Py.exceptions import GoResourceValidationError

    system = GoSystem()
    if su.connect_system(system, args.ip, args.port):
        return su.ERROR_STATUS
    if su.verify_connection(system) == su.ERROR_STATUS:
        system.disconnect()
        return su.ERROR_STATUS
    try:
        system_res = system.resource("/system")
        full_schema = system_res.schema()
        print(f"Schema type: {full_schema.get('type')}")
        props = full_schema.get("properties") or {}
        print("Top-level properties:")
        for name, meta in props.items():
            print(f"  {name} ({meta.get('type', 'unknown')})")

        _print_schema("runState", system_res.schema_for("/runState"))

        sensor = system.resource(PATHS.sensor_path)
        _print_schema("singleExposure", sensor.schema_for("/parameters/exposureSettings/singleExposure"))

        errors: list[str] = []
        ok = sensor.validate("/parameters/exposureSettings/singleExposure", 1000, errors)
        print(f"Validate exposure=1000: {'PASS' if ok else 'FAIL'}")
        errors.clear()
        ok = sensor.validate("/parameters/exposureSettings/singleExposure", 999999, errors)
        print(f"Validate exposure=999999: {'PASS' if ok else 'FAIL'}")
        for err in errors:
            print(f"  Error: {err}")

        sensor.enable_validation(True)
        try:
            sensor.set_int("/parameters/exposureSettings/exposureMode", 0)
            print("SetInt(exposureMode, 0): OK")
        except GoResourceValidationError as exc:
            print(f"Validation error: {exc}")
        try:
            sensor.set_int("/parameters/exposureSettings/exposureMode", 99)
            print("SetInt(exposureMode, 99): OK (unexpected)")
        except GoResourceValidationError as exc:
            print(f"SetInt(exposureMode, 99): caught {exc}")
        sensor.enable_validation(False)

        mgr = system.resource_manager()
        print(f"AutoValidation: {mgr.auto_validation()}")
        scanner = system.resource(PATHS.scanner_path)
        print(f"Scanner validation enabled: {scanner.is_validation_enabled()}")
        _print_schema("trigger source", scanner.schema_for("/parameters/triggerSettings/source"))
    finally:
        system.disconnect()
    return su.OK_STATUS


def main() -> int:
    return su.run_main("GoResource schema sample.", _main, default_ip=SYSTEM_IP, default_port=CONTROL_PORT)


if __name__ == "__main__":
    raise SystemExit(main())
