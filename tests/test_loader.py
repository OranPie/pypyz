from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pvz.content.loader import ModLoader
from pvz.errors import MissingBaseModError


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


class LoaderTests(unittest.TestCase):
    def test_missing_base_mod_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods = Path(tmp)
            other = mods / "my.mod"
            other.mkdir(parents=True)
            (other / "mod.json").write_text(
                json.dumps(
                    {
                        "id": "my.mod",
                        "version": "1.0.0",
                        "title": "My Mod",
                        "engine_api": "1.0",
                    }
                ),
                encoding="utf-8",
            )

            loader = ModLoader(mods, schema_root=SCHEMAS)
            with self.assertRaises(MissingBaseModError):
                loader.load()

    def test_loads_real_base_mod(self) -> None:
        loader = ModLoader(ROOT / "mods", schema_root=SCHEMAS)
        loaded = loader.load()
        self.assertIn("pvz.base", loaded.mod_ids)
        self.assertIn("plants", loaded.registry.categories)
        self.assertIn("projectiles", loaded.registry.categories)
        self.assertIn("mini_games", loaded.registry.categories)
        self.assertIn("pvz.base:plants:peashooter", loaded.registry.categories["plants"])

    def test_upgrade_plants_define_explicit_upgrade_block(self) -> None:
        loader = ModLoader(ROOT / "mods", schema_root=SCHEMAS)
        loaded = loader.load()
        plants = loaded.registry.categories["plants"].values()

        for item in plants:
            data = item.data
            has_upgrade_tag = "upgrade" in data.get("tags", [])
            has_upgrade_block = bool(data.get("upgrade"))
            if has_upgrade_tag:
                self.assertTrue(
                    has_upgrade_block,
                    msg=f"{item.id} has upgrade tag but no upgrade block",
                )
            if has_upgrade_block:
                upgrade = data["upgrade"]
                self.assertGreaterEqual(upgrade.get("consume", 0), 1, msg=item.id)
                self.assertTrue(upgrade.get("from"), msg=item.id)


if __name__ == "__main__":
    unittest.main()
