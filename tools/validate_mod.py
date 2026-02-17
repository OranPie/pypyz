from __future__ import annotations

import argparse
import json
from pathlib import Path

from pvz.content.loader import CATEGORY_SCHEMA
from pvz.content.manifest import parse_manifest
from pvz.content.schema_validator import SchemaStore, validate_against_schema


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a mod folder")
    parser.add_argument("mod_path", type=Path)
    parser.add_argument("--schemas", type=Path, default=Path("schemas"))
    args = parser.parse_args()

    mod_path = args.mod_path
    manifest_payload = json.loads((mod_path / "mod.json").read_text(encoding="utf-8"))
    schemas = SchemaStore(args.schemas)
    validate_against_schema(manifest_payload, schemas.get("manifest"), source=str(mod_path / "mod.json"))

    manifest = parse_manifest(mod_path)

    content_root = mod_path / "content"
    for file_path in sorted(content_root.rglob("*.json")):
        rel = file_path.relative_to(content_root)
        category = rel.parts[0] if rel.parts else "misc"
        schema_name = CATEGORY_SCHEMA.get(category)
        if not schema_name:
            continue
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if ":" not in str(payload.get("id", "")):
            payload["id"] = f"{manifest.id}:{category}:{payload.get('id', rel.stem)}"
        validate_against_schema(payload, schemas.get(schema_name), source=str(file_path))

    print(f"OK: {manifest.id} ({manifest.version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
