"""Public JSON and internal Python key conversion helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


def _snake_key_to_camel(key: str) -> str:
    parts = key.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _camel_key_to_snake(key: str) -> str:
    chars: list[str] = []
    for char in key:
        if char.isupper():
            chars.append("_")
            chars.append(char.lower())
        else:
            chars.append(char)
    return "".join(chars).lstrip("_")


def to_camel(value: JsonValue) -> JsonValue:
    if isinstance(value, Mapping):
        return {_snake_key_to_camel(str(key)): to_camel(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_camel(item) for item in value]
    return value


def to_snake(value: JsonValue) -> JsonValue:
    if isinstance(value, Mapping):
        return {_camel_key_to_snake(str(key)): to_snake(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_snake(item) for item in value]
    return value
