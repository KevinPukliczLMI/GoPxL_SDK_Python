"""GoSchemaValidator - mirrors GoPxLSdk::GoSchemaValidator."""

from __future__ import annotations

import math
from typing import Any

from .exceptions import GoResourceError
from .json_pointer import is_numeric_segment, normalize_path, split_path


class GoSchemaValidator:
    @staticmethod
    def schema_for_path(full_schema: dict[str, Any], path: str) -> dict[str, Any]:
        segments = split_path(normalize_path(path))
        if not segments:
            return full_schema

        current: Any = full_schema
        for segment in segments:
            schema_type = _schema_type(current)
            if schema_type in ("object", ""):
                props = current.get("properties")
                if not isinstance(props, dict) or segment not in props:
                    raise GoResourceError(
                        f'GoSchemaValidator.schema_for_path: cannot resolve segment "{segment}" '
                        f"(no properties/{segment})"
                    )
                current = props[segment]
            elif schema_type == "array":
                if not is_numeric_segment(segment):
                    raise GoResourceError(
                        f'GoSchemaValidator.schema_for_path: expected numeric index for array, '
                        f'got "{segment}"'
                    )
                items = current.get("items")
                if items is None:
                    raise GoResourceError(
                        f'GoSchemaValidator.schema_for_path: cannot resolve array index "{segment}" '
                        "(no items keyword)"
                    )
                if isinstance(items, list):
                    current = items[int(segment)]
                else:
                    current = items
            else:
                raise GoResourceError(
                    f'GoSchemaValidator.schema_for_path: cannot navigate into schema type '
                    f'"{schema_type}" at segment "{segment}"'
                )
        return current

    @staticmethod
    def validate(value: Any, schema_node: dict[str, Any], errors: list[str] | None = None) -> bool:
        if errors is None:
            errors = []
        initial = len(errors)

        if schema_node.get("readOnly"):
            errors.append("property is read-only")
            return False

        expected_type = _schema_type(schema_node)
        if expected_type and not _check_type(value, expected_type):
            errors.append(f"type mismatch: expected {expected_type}, got {_value_type_name(value)}")
            return False

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            _validate_numeric(value, schema_node, errors)

        if isinstance(value, str):
            _validate_string(value, schema_node, errors)

        if isinstance(value, list):
            _validate_array(value, schema_node, errors)

        if isinstance(value, dict):
            _validate_object(value, schema_node, errors)

        if value is not None and not isinstance(value, (dict, list)):
            _validate_enum(value, schema_node, errors)

        return len(errors) == initial


def _schema_type(schema_node: dict[str, Any]) -> str:
    schema_type = schema_node.get("type")
    return str(schema_type) if schema_type is not None else ""


def _value_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "unknown"


def _check_type(value: Any, expected_type: str) -> bool:
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type in ("string", "binary"):
        return isinstance(value, str)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    return True


def _validate_numeric(value: float, schema_node: dict[str, Any], errors: list[str]) -> None:
    if "minimum" in schema_node and value < schema_node["minimum"]:
        errors.append(f"value {value} is less than minimum {schema_node['minimum']}")
    if "maximum" in schema_node and value > schema_node["maximum"]:
        errors.append(f"value {value} exceeds maximum {schema_node['maximum']}")
    if "exclusiveMinimum" in schema_node and value <= schema_node["exclusiveMinimum"]:
        errors.append(
            f"value {value} is not greater than exclusiveMinimum {schema_node['exclusiveMinimum']}"
        )
    if "exclusiveMaximum" in schema_node and value >= schema_node["exclusiveMaximum"]:
        errors.append(
            f"value {value} is not less than exclusiveMaximum {schema_node['exclusiveMaximum']}"
        )
    multiple_of = schema_node.get("multipleOf")
    if multiple_of:
        remainder = math.fmod(float(value), float(multiple_of))
        if abs(remainder) > 1e-9 and abs(remainder - float(multiple_of)) > 1e-9:
            errors.append(f"value {value} is not a multiple of {multiple_of}")


def _validate_string(value: str, schema_node: dict[str, Any], errors: list[str]) -> None:
    if "minLength" in schema_node and len(value) < schema_node["minLength"]:
        errors.append(f"string length {len(value)} is less than minLength {schema_node['minLength']}")
    if "maxLength" in schema_node and len(value) > schema_node["maxLength"]:
        errors.append(f"string length {len(value)} exceeds maxLength {schema_node['maxLength']}")


def _validate_array(value: list[Any], schema_node: dict[str, Any], errors: list[str]) -> None:
    if "minItems" in schema_node and len(value) < schema_node["minItems"]:
        errors.append(f"array size {len(value)} is less than minItems {schema_node['minItems']}")
    if "maxItems" in schema_node and len(value) > schema_node["maxItems"]:
        errors.append(f"array size {len(value)} exceeds maxItems {schema_node['maxItems']}")


def _validate_object(value: dict[str, Any], schema_node: dict[str, Any], errors: list[str]) -> None:
    required = schema_node.get("required")
    if isinstance(required, list):
        for name in required:
            if name not in value:
                errors.append(f'missing required property "{name}"')


def _validate_enum(value: Any, schema_node: dict[str, Any], errors: list[str]) -> None:
    enum_values = schema_node.get("enum")
    if not isinstance(enum_values, list):
        return
    for candidate in enum_values:
        if candidate == value:
            return
        if isinstance(value, (int, float)) and isinstance(candidate, (int, float)):
            if abs(float(value) - float(candidate)) < 1e-9:
                return
    errors.append("value is not in the allowed enum set")