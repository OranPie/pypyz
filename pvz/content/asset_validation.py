from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pvz.errors import AssetValidationError


def _is_http_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _validate_local_asset_path(value: str, *, mod_root: Path, source: str) -> None:
    asset_path = Path(value)
    if asset_path.is_absolute():
        raise AssetValidationError(f"{source}: absolute asset path is not allowed: {value}")
    if ".." in asset_path.parts:
        raise AssetValidationError(f"{source}: parent traversal is not allowed: {value}")
    if not value.startswith("assets/"):
        raise AssetValidationError(f"{source}: local asset refs must start with assets/: {value}")

    resolved = (mod_root / asset_path).resolve()
    mod_root_resolved = mod_root.resolve()
    if mod_root_resolved not in resolved.parents and resolved != mod_root_resolved:
        raise AssetValidationError(f"{source}: asset path escapes mod root: {value}")
    if not resolved.exists():
        raise AssetValidationError(f"{source}: missing asset file: {value}")


def _validate_asset_ref(value: str, *, mod_root: Path, source: str) -> None:
    if _is_http_url(value):
        return
    if "://" in value:
        raise AssetValidationError(f"{source}: unsupported URL scheme: {value}")
    _validate_local_asset_path(value, mod_root=mod_root, source=source)


def _validate_many(values: Iterable[str], *, mod_root: Path, source: str) -> None:
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise AssetValidationError(f"{source}[{index}]: expected string, got {type(value).__name__}")
        _validate_asset_ref(value, mod_root=mod_root, source=f"{source}[{index}]")


def validate_content_asset_refs(
    payload: dict,
    *,
    category: str,
    mod_root: Path,
    source: str,
) -> None:
    if category == "media_resources":
        _validate_many(payload.get("textures", []), mod_root=mod_root, source=f"{source}.textures")
        _validate_many(payload.get("sounds", []), mod_root=mod_root, source=f"{source}.sounds")
        _validate_many(payload.get("page_sources", []), mod_root=mod_root, source=f"{source}.page_sources")
        raw_snapshot = payload.get("raw_snapshot")
        if raw_snapshot is not None:
            if not isinstance(raw_snapshot, str):
                raise AssetValidationError(f"{source}.raw_snapshot: expected string")
            _validate_asset_ref(raw_snapshot, mod_root=mod_root, source=f"{source}.raw_snapshot")
        return

    if category == "animation_configs":
        frames = payload.get("frames", [])
        for frame_index, frame in enumerate(frames):
            texture = frame.get("texture")
            if not isinstance(texture, str):
                raise AssetValidationError(
                    f"{source}.frames[{frame_index}].texture: expected string"
                )
            _validate_asset_ref(
                texture,
                mod_root=mod_root,
                source=f"{source}.frames[{frame_index}].texture",
            )

        sound_events = payload.get("sound_events", [])
        for event_index, event in enumerate(sound_events):
            sound_url = event.get("sound_url")
            if not isinstance(sound_url, str):
                raise AssetValidationError(
                    f"{source}.sound_events[{event_index}].sound_url: expected string"
                )
            _validate_asset_ref(
                sound_url,
                mod_root=mod_root,
                source=f"{source}.sound_events[{event_index}].sound_url",
            )
