import glob
import json
import re
import unittest
from pathlib import Path


LEVEL_DIR = Path("mods/pvz.base/content/levels")
ZOMBIE_DIR = Path("mods/pvz.base/content/zombies")
WEB_ALIGNMENT_RAW = Path("mods/pvz.base/assets/indexes/alignment/pvz1_levels_fandom_raw.json")

ZOMBIE_NAME_ALIASES = {
    "zombie": "basic",
    "drzomboss": "doctor_zomboss",
    "drzombosszombie": "doctor_zomboss",
    "zombotanywallnutzombie": "zombotany_wallnut",
    "zombotanytallnutzombie": "zombotany_tallnut",
}


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def build_zombie_lookup():
    lookup = dict(ZOMBIE_NAME_ALIASES)
    for path in sorted(glob.glob(str(ZOMBIE_DIR / "*.json"))):
        with open(path, "r", encoding="utf-8") as fh:
            zombie = json.load(fh)
        lookup[normalize(zombie.get("name", zombie["id"]))] = zombie["id"]
    return lookup


class LevelAlignmentTest(unittest.TestCase):
    def test_total_adventure_levels(self):
        levels = sorted(glob.glob(str(LEVEL_DIR / "*.json")))
        self.assertEqual(len(levels), 50)

    def test_web_snapshot_pool_and_flag_alignment(self):
        self.assertTrue(WEB_ALIGNMENT_RAW.exists())
        with WEB_ALIGNMENT_RAW.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        self.assertEqual(len(raw.get("levels", [])), 50)

        zombie_lookup = build_zombie_lookup()
        level_by_id = {}
        for path in sorted(glob.glob(str(LEVEL_DIR / "*.json"))):
            with open(path, "r", encoding="utf-8") as fh:
                level = json.load(fh)
            level_by_id[level["id"]] = level

        for entry in raw["levels"]:
            level_id = entry["level_id"]
            self.assertIn(level_id, level_by_id)
            level = level_by_id[level_id]

            flags_count = entry.get("flags_count")
            if isinstance(flags_count, int):
                self.assertEqual(level.get("flags_count"), flags_count, msg=level_id)

            expected_pool = []
            for zombie_name in entry.get("first_play_zombies", []):
                zombie_id = zombie_lookup.get(normalize(zombie_name))
                if zombie_id is None:
                    continue
                fqid = f"pvz.base:zombies:{zombie_id}"
                if fqid not in expected_pool:
                    expected_pool.append(fqid)

            # Some special levels do not expose a first-play table on the source page.
            if expected_pool:
                self.assertEqual(set(level.get("zombie_pool", [])), set(expected_pool), msg=level_id)

    def test_special_level_overrides(self):
        with open(LEVEL_DIR / "fog_5.json", "r", encoding="utf-8") as fh:
            fog_5 = json.load(fh)
        with open(LEVEL_DIR / "roof_10.json", "r", encoding="utf-8") as fh:
            roof_10 = json.load(fh)
        self.assertEqual(fog_5.get("area_override"), "night_pool_minigame")
        self.assertEqual(roof_10.get("area_override"), "night_roof_boss")


if __name__ == "__main__":
    unittest.main()
