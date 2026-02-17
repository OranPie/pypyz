from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pvz.errors import PatchError
from pvz.models import ContentRegistry


def _decode_pointer(path: str) -> list[str]:
    if path in ("", "/"):
        return []
    if not path.startswith("/"):
        raise PatchError(f"invalid json pointer: {path}")
    return [p.replace("~1", "/").replace("~0", "~") for p in path[1:].split("/")]


def _navigate(container: Any, pointer: str) -> tuple[Any, str | int | None]:
    tokens = _decode_pointer(pointer)
    if not tokens:
        return (None, None)

    parent = container
    for token in tokens[:-1]:
        if isinstance(parent, dict):
            if token not in parent:
                raise PatchError(f"missing object key while navigating pointer: {token}")
            parent = parent[token]
        elif isinstance(parent, list):
            if token == "-":
                raise PatchError("cannot traverse list with - token")
            index = int(token)
            if index >= len(parent):
                raise PatchError(f"list index out of bounds: {index}")
            parent = parent[index]
        else:
            raise PatchError("cannot navigate through scalar value")

    last = tokens[-1]
    if isinstance(parent, list):
        if last == "-":
            return parent, "-"
        return parent, int(last)
    return parent, last


def _get_target(registry: ContentRegistry, target: str) -> dict[str, Any]:
    for entries in registry.categories.values():
        if target in entries:
            return entries[target].data
    raise PatchError(f"patch target not found: {target}")


def _apply_single(data: dict[str, Any], op: dict[str, Any]) -> None:
    operation = op.get("op")
    pointer = op.get("path", "/")

    if operation not in {"add", "replace", "remove", "merge", "append"}:
        raise PatchError(f"unsupported patch op: {operation}")

    if pointer in ("", "/") and operation == "replace":
        value = op.get("value")
        if not isinstance(value, dict):
            raise PatchError("root replace requires object value")
        data.clear()
        data.update(value)
        return

    if operation == "merge":
        parent, key = _navigate(data, pointer)
        target = data if key is None else (parent[key] if isinstance(parent, dict) else parent[key])
        value = op.get("value")
        if not isinstance(target, dict) or not isinstance(value, dict):
            raise PatchError("merge requires object target and object value")
        target.update(value)
        return

    if operation == "append":
        parent, key = _navigate(data, pointer)
        target = data if key is None else (parent[key] if isinstance(parent, dict) else parent[key])
        if not isinstance(target, list):
            raise PatchError("append requires list target")
        target.append(op.get("value"))
        return

    parent, key = _navigate(data, pointer)

    if key is None:
        raise PatchError(f"operation `{operation}` cannot target root path directly")

    if isinstance(parent, dict):
        if operation == "remove":
            if key not in parent:
                raise PatchError(f"cannot remove missing key: {key}")
            del parent[key]
            return
        parent[key] = op.get("value")
        return

    if isinstance(parent, list):
        if key == "-":
            if operation in {"add", "replace"}:
                parent.append(op.get("value"))
                return
            raise PatchError("only add/replace support - index")

        if not isinstance(key, int):
            raise PatchError("invalid list key")
        if operation == "remove":
            if key >= len(parent):
                raise PatchError(f"cannot remove list index {key}")
            parent.pop(key)
            return

        if operation == "add":
            if key > len(parent):
                raise PatchError(f"cannot insert beyond list end: {key}")
            parent.insert(key, op.get("value"))
            return

        if operation == "replace":
            if key >= len(parent):
                raise PatchError(f"cannot replace missing list index: {key}")
            parent[key] = op.get("value")
            return

    raise PatchError("unsupported patch target type")


def apply_patches(registry: ContentRegistry, patch_file: Path) -> None:
    payload = json.loads(patch_file.read_text(encoding="utf-8"))
    ops = payload.get("ops", payload)
    if not isinstance(ops, list):
        raise PatchError(f"patch file must contain list or object with `ops`: {patch_file}")

    for op in ops:
        if not isinstance(op, dict) or "target" not in op or "op" not in op:
            raise PatchError(f"invalid patch operation in {patch_file}")
        target = str(op["target"])
        data = _get_target(registry, target)
        _apply_single(data, op)
