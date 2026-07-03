"""JSON pointer helpers for GoResource and GoSchemaValidator."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class JsonPointerError(KeyError):
    pass


def normalize_path(path: str) -> str:
    if not path:
        return path
    return path if path.startswith("/") else f"/{path}"


def split_path(path: str) -> list[str]:
    if not path:
        return []
    start = 1 if path[0] == "/" else 0
    segments: list[str] = []
    while start < len(path):
        end = path.find("/", start)
        if end == -1:
            segments.append(path[start:])
            break
        segments.append(path[start:end])
        start = end + 1
    return segments


def get_at(data: Any, path: str) -> Any:
    if not path or path == "/":
        return data
    current = data
    for segment in split_path(normalize_path(path)):
        if isinstance(current, dict):
            if segment not in current:
                raise JsonPointerError(f"key not found: {segment}")
            current = current[segment]
        elif isinstance(current, list):
            if not segment.isdigit():
                raise JsonPointerError(f"expected numeric index, got {segment!r}")
            index = int(segment)
            current = current[index]
        else:
            raise JsonPointerError(f"cannot navigate into {type(current).__name__}")
    return current


def set_at(data: dict[str, Any], path: str, value: Any) -> None:
    normalized = normalize_path(path)
    segments = split_path(normalized)
    if not segments:
        raise JsonPointerError("cannot set root path")
    current: Any = data
    for segment in segments[:-1]:
        if segment not in current or not isinstance(current[segment], dict):
            current[segment] = {}
        current = current[segment]
    current[segments[-1]] = value


def merge_patch(target: dict[str, Any], patch: dict[str, Any]) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            merge_patch(target[key], value)
        else:
            target[key] = deepcopy(value)


def is_numeric_segment(segment: str) -> bool:
    return bool(segment) and segment.isdigit()