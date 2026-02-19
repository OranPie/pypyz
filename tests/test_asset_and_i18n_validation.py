from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pvz.content.loader import ModLoader
from pvz.errors import AssetValidationError, LocalizationValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _init_base_mod(mods: Path) -> Path:
    base = mods / "pvz.base"
    base.mkdir(parents=True, exist_ok=True)
    _write_json(
        base / "mod.json",
        {
            "id": "pvz.base",
            "version": "1.0.0",
            "title": "Base",
            "engine_api": "1.0",
        },
    )
    return base


class AssetAndI18nValidationTests(unittest.TestCase):
    def test_media_resource_raw_snapshot_missing_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods = Path(tmp)
            base = _init_base_mod(mods)
            _write_json(
                base / "content" / "media_resources" / "index.json",
                {
                    "id": "media_index",
                    "source": "test",
                    "textures": [],
                    "sounds": [],
                    "raw_snapshot": "assets/indexes/media/missing.json",
                },
            )

            loader = ModLoader(mods, schema_root=SCHEMAS)
            with self.assertRaises(AssetValidationError):
                loader.load()

    def test_media_resource_raw_snapshot_existing_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods = Path(tmp)
            base = _init_base_mod(mods)
            raw = base / "assets" / "indexes" / "media" / "raw.json"
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text("{}", encoding="utf-8")

            _write_json(
                base / "content" / "media_resources" / "index.json",
                {
                    "id": "media_index",
                    "source": "test",
                    "textures": ["https://example.com/tex.png"],
                    "sounds": ["https://example.com/sfx.ogg"],
                    "raw_snapshot": "assets/indexes/media/raw.json",
                },
            )

            loader = ModLoader(mods, schema_root=SCHEMAS)
            loaded = loader.load()
            self.assertIn("media_resources", loaded.registry.categories)
            self.assertIn(
                "pvz.base:media_resources:media_index",
                loaded.registry.categories["media_resources"],
            )

    def test_animation_texture_parent_traversal_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods = Path(tmp)
            base = _init_base_mod(mods)
            _write_json(
                base / "content" / "animation_configs" / "bad.json",
                {
                    "id": "bad_anim",
                    "target_id": "pvz.base:zombies:basic",
                    "fps": 10,
                    "loop": True,
                    "frames": [
                        {
                            "frame": 0,
                            "texture": "assets/../escape.png",
                            "duration_ms": 100,
                        }
                    ],
                    "sound_events": [],
                },
            )

            loader = ModLoader(mods, schema_root=SCHEMAS)
            with self.assertRaises(AssetValidationError):
                loader.load()

    def test_localization_extra_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods = Path(tmp)
            base = _init_base_mod(mods)
            _write_json(base / "localization" / "en.json", {"menu.start": "Start"})
            _write_json(
                base / "localization" / "zh-CN.json",
                {
                    "menu.start": "开始",
                    "menu.extra_only": "额外",
                },
            )

            loader = ModLoader(mods, schema_root=SCHEMAS)
            with self.assertRaises(LocalizationValidationError):
                loader.load()

    def test_localization_matching_keys_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods = Path(tmp)
            base = _init_base_mod(mods)
            _write_json(
                base / "localization" / "en.json",
                {"menu.start": "Start", "menu.shop": "Shop"},
            )
            _write_json(
                base / "localization" / "zh-CN.json",
                {"menu.start": "开始", "menu.shop": "商店"},
            )

            loader = ModLoader(mods, schema_root=SCHEMAS)
            loaded = loader.load()
            self.assertEqual(loaded.mod_ids, ["pvz.base"])


if __name__ == "__main__":
    unittest.main()
