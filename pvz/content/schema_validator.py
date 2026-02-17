from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pvz.errors import SchemaValidationError


class SchemaStore:
    def __init__(self, schema_root: Path):
        self.schema_root = schema_root
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, name: str) -> dict[str, Any]:
        if name not in self._cache:
            path = self.schema_root / f"{name}.schema.json"
            if not path.exists():
                raise SchemaValidationError(f"missing schema: {path}")
            self._cache[name] = json.loads(path.read_text(encoding="utf-8"))
        return self._cache[name]


def _check_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def validate_against_schema(
    payload: Any,
    schema: dict[str, Any],
    *,
    source: str,
) -> None:
    schema_type = schema.get("type")
    if schema_type and not _check_type(payload, schema_type):
        raise SchemaValidationError(
            f"{source}: expected {schema_type}, got {type(payload).__name__}"
        )

    if schema_type == "object":
        required = schema.get("required", [])
        for key in required:
            if key not in payload:
                raise SchemaValidationError(f"{source}: missing key `{key}`")

        properties = schema.get("properties", {})
        for key, value in payload.items():
            if key not in properties:
                continue
            validate_against_schema(value, properties[key], source=f"{source}.{key}")

    if schema_type == "array":
        item_schema = schema.get("items")
        if item_schema is None:
            return
        for index, value in enumerate(payload):
            validate_against_schema(value, item_schema, source=f"{source}[{index}]")

    enum_values = schema.get("enum")
    if enum_values is not None and payload not in enum_values:
        raise SchemaValidationError(
            f"{source}: value `{payload}` not in enum {enum_values}"
        )
