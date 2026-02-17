from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pvz.errors import ManifestError
from pvz.models import Dependency, ModManifest


REQUIRED_FIELDS = {"id", "version", "title", "engine_api"}


def _parse_dependencies(raw: Any) -> tuple[Dependency, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ManifestError("dependencies must be a list")
    deps: list[Dependency] = []
    for item in raw:
        if not isinstance(item, dict) or "id" not in item:
            raise ManifestError("dependency items must be objects with `id`")
        deps.append(Dependency(id=str(item["id"]), version=str(item.get("version", ""))))
    return tuple(deps)


def _parse_str_list(raw: Any, field_name: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(x, str) for x in raw):
        raise ManifestError(f"{field_name} must be a list of strings")
    return tuple(raw)


def parse_manifest(path: Path) -> ModManifest:
    manifest_path = path / "mod.json"
    if not manifest_path.exists():
        raise ManifestError(f"missing manifest: {manifest_path}")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    missing = REQUIRED_FIELDS - payload.keys()
    if missing:
        raise ManifestError(f"manifest missing required fields: {sorted(missing)}")

    entrypoints = payload.get("entrypoints", {})
    if not isinstance(entrypoints, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in entrypoints.items()
    ):
        raise ManifestError("entrypoints must be an object of string:string")

    return ModManifest(
        id=str(payload["id"]),
        version=str(payload["version"]),
        title=str(payload["title"]),
        engine_api=str(payload["engine_api"]),
        requires=_parse_dependencies(payload.get("requires")),
        conflicts=_parse_dependencies(payload.get("conflicts")),
        load_before=_parse_str_list(payload.get("load_before"), "load_before"),
        load_after=_parse_str_list(payload.get("load_after"), "load_after"),
        capabilities=_parse_str_list(payload.get("capabilities"), "capabilities"),
        entrypoints=entrypoints,
    )
