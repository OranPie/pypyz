from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pvz.content.loader import ModLoader
from pvz.errors import DependencyError


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class DependencyAndPatchTests(unittest.TestCase):
    def test_dependency_version_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods = Path(tmp)

            _write_json(
                mods / "pvz.base" / "mod.json",
                {
                    "id": "pvz.base",
                    "version": "1.0.0",
                    "title": "Base",
                    "engine_api": "1.0",
                },
            )
            _write_json(
                mods / "pvz.base" / "content" / "plants" / "pea.json",
                {
                    "id": "pea",
                    "name": "Pea",
                    "cost": 100,
                    "cooldown": 7.5,
                    "max_hp": 300,
                    "damage": 20,
                },
            )

            _write_json(
                mods / "addon" / "mod.json",
                {
                    "id": "addon",
                    "version": "1.0.0",
                    "title": "Addon",
                    "engine_api": "1.0",
                    "requires": [{"id": "pvz.base", "version": ">=2.0.0"}],
                },
            )

            loader = ModLoader(mods, schema_root=SCHEMAS)
            with self.assertRaises(DependencyError):
                loader.load()

    def test_explicit_patch_overrides_base_damage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods = Path(tmp)

            _write_json(
                mods / "pvz.base" / "mod.json",
                {
                    "id": "pvz.base",
                    "version": "1.0.0",
                    "title": "Base",
                    "engine_api": "1.0",
                },
            )
            _write_json(
                mods / "pvz.base" / "content" / "plants" / "peashooter.json",
                {
                    "id": "peashooter",
                    "name": "Peashooter",
                    "cost": 100,
                    "cooldown": 7.5,
                    "max_hp": 300,
                    "damage": 20,
                },
            )

            _write_json(
                mods / "addon" / "mod.json",
                {
                    "id": "addon",
                    "version": "1.1.0",
                    "title": "Balance Patch",
                    "engine_api": "1.0",
                    "requires": [{"id": "pvz.base", "version": "^1.0.0"}],
                    "load_after": ["pvz.base"],
                },
            )
            _write_json(
                mods / "addon" / "patches" / "buff.json",
                {
                    "ops": [
                        {
                            "target": "pvz.base:plants:peashooter",
                            "op": "replace",
                            "path": "/damage",
                            "value": 35,
                        }
                    ]
                },
            )

            loader = ModLoader(mods, schema_root=SCHEMAS)
            loaded = loader.load()
            pea = loaded.registry.get("plants", "pvz.base:plants:peashooter").data
            self.assertEqual(pea["damage"], 35)
            self.assertEqual(loaded.mod_ids, ["pvz.base", "addon"])


if __name__ == "__main__":
    unittest.main()
