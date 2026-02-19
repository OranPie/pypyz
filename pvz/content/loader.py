from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pvz.content.dependency import resolve_load_order
from pvz.content.manifest import parse_manifest
from pvz.content.patcher import apply_patches
from pvz.content.schema_validator import SchemaStore, validate_against_schema
from pvz.errors import ManifestError, MissingBaseModError
from pvz.models import ContentItem, ContentRegistry, ModPackage


CATEGORY_SCHEMA = {
    "plants": "plant",
    "zombies": "zombie",
    "projectiles": "projectile",
    "status_effects": "status_effect",
    "levels": "level",
    "waves": "wave",
    "map_nodes": "map_node",
    "mini_games": "minigame",
    "puzzle_levels": "puzzle_level",
    "survival_levels": "survival_level",
    "shop": "shop_item",
    "almanac": "almanac_entry",
    "zen": "zen_item",
    "unlock_rules": "unlock_rule",
    "achievements": "achievement",
    "economy": "economy",
    "ui_screens": "ui_screen",
    "audio_events": "audio_event",
    "media_resources": "media_resource",
    "animation_configs": "animation_config",
}


@dataclass
class LoadedGameData:
    mods: list[ModPackage]
    registry: ContentRegistry

    @property
    def mod_ids(self) -> list[str]:
        return [mod.manifest.id for mod in self.mods]


class ModLoader:
    def __init__(
        self,
        mods_dir: Path,
        *,
        schema_root: Path,
        required_base_mod: str = "pvz.base",
    ) -> None:
        self.mods_dir = mods_dir
        self.required_base_mod = required_base_mod
        self.schemas = SchemaStore(schema_root)

    def discover_mods(self) -> dict[str, ModPackage]:
        mods: dict[str, ModPackage] = {}
        if not self.mods_dir.exists():
            raise ManifestError(f"mods directory does not exist: {self.mods_dir}")

        for child in sorted(self.mods_dir.iterdir()):
            if not child.is_dir():
                continue
            manifest_path = child / "mod.json"
            if not manifest_path.exists():
                continue

            manifest = parse_manifest(child)
            if manifest.id in mods:
                raise ManifestError(f"duplicate mod id: {manifest.id}")
            mods[manifest.id] = ModPackage(manifest=manifest, path=child)

        if self.required_base_mod not in mods:
            raise MissingBaseModError(
                f"required base mod `{self.required_base_mod}` is missing"
            )

        return mods

    def load(self) -> LoadedGameData:
        mod_map = self.discover_mods()
        ordered_mods = resolve_load_order(mod_map)
        registry = ContentRegistry()

        for mod in ordered_mods:
            self._load_content_for_mod(mod, registry)

        for mod in ordered_mods:
            self._apply_patches_for_mod(mod, registry)

        return LoadedGameData(mods=ordered_mods, registry=registry)

    def _load_content_for_mod(self, mod: ModPackage, registry: ContentRegistry) -> None:
        content_root = mod.path / "content"
        if not content_root.exists():
            return

        for file_path in sorted(content_root.rglob("*.json")):
            rel = file_path.relative_to(content_root)
            category = rel.parts[0] if rel.parts else "misc"
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ManifestError(f"content file must be object: {file_path}")

            explicit_id = str(payload.get("id", rel.stem))
            if ":" in explicit_id:
                item_id = explicit_id
            else:
                item_id = f"{mod.manifest.id}:{category}:{explicit_id}"
            payload["id"] = item_id

            schema_name = CATEGORY_SCHEMA.get(category)
            if schema_name:
                schema = self.schemas.get(schema_name)
                validate_against_schema(payload, schema, source=str(file_path))

            registry.add(
                ContentItem(
                    id=item_id,
                    category=category,
                    data=payload,
                    source_mod=mod.manifest.id,
                    source_path=file_path,
                )
            )

    def _apply_patches_for_mod(self, mod: ModPackage, registry: ContentRegistry) -> None:
        patch_root = mod.path / "patches"
        if not patch_root.exists():
            return

        for patch_file in sorted(patch_root.rglob("*.json")):
            apply_patches(registry, patch_file)
