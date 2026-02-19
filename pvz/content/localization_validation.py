from __future__ import annotations

import json
from pathlib import Path

from pvz.errors import LocalizationValidationError


def validate_localization_files(mod_root: Path) -> None:
    loc_root = mod_root / "localization"
    if not loc_root.exists():
        return

    bundles: dict[str, dict[str, str]] = {}
    for path in sorted(loc_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise LocalizationValidationError(f"{path}: localization bundle must be an object")
        for key, value in payload.items():
            if not isinstance(key, str):
                raise LocalizationValidationError(f"{path}: localization key must be string")
            if not isinstance(value, str):
                raise LocalizationValidationError(
                    f"{path}: localization value for `{key}` must be string"
                )
        bundles[path.name] = payload

    if "en.json" not in bundles:
        return

    base_keys = set(bundles["en.json"].keys())
    for name, bundle in bundles.items():
        if name == "en.json":
            continue
        keys = set(bundle.keys())
        missing = sorted(base_keys - keys)
        extra = sorted(keys - base_keys)
        if missing:
            sample = ", ".join(missing[:8])
            raise LocalizationValidationError(
                f"{loc_root / name}: missing {len(missing)} key(s) vs en.json (sample: {sample})"
            )
        if extra:
            sample = ", ".join(extra[:8])
            raise LocalizationValidationError(
                f"{loc_root / name}: has {len(extra)} extra key(s) not in en.json (sample: {sample})"
            )
