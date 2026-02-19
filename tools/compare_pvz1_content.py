#!/usr/bin/env python3
"""Compare pvz.base content coverage with canonical PvZ1 lists."""

from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple


CANONICAL: Dict[str, List[str]] = {
    "plants": [
        "Peashooter",
        "Sunflower",
        "Cherry Bomb",
        "Wall-nut",
        "Potato Mine",
        "Snow Pea",
        "Chomper",
        "Repeater",
        "Puff-shroom",
        "Sun-shroom",
        "Fume-shroom",
        "Grave Buster",
        "Hypno-shroom",
        "Scaredy-shroom",
        "Ice-shroom",
        "Doom-shroom",
        "Lily Pad",
        "Squash",
        "Threepeater",
        "Tangle Kelp",
        "Jalapeno",
        "Spikeweed",
        "Torchwood",
        "Tall-nut",
        "Sea-shroom",
        "Plantern",
        "Cactus",
        "Blover",
        "Split Pea",
        "Starfruit",
        "Pumpkin",
        "Magnet-shroom",
        "Cabbage-pult",
        "Flower Pot",
        "Kernel-pult",
        "Coffee Bean",
        "Garlic",
        "Umbrella Leaf",
        "Marigold",
        "Melon-pult",
        "Gatling Pea",
        "Twin Sunflower",
        "Gloom-shroom",
        "Cattail",
        "Winter Melon",
        "Gold Magnet",
        "Spikerock",
        "Cob Cannon",
        "Imitater",
    ],
    "zombies": [
        "Regular Zombie",
        "Flag Zombie",
        "Conehead Zombie",
        "Pole Vaulting Zombie",
        "Buckethead Zombie",
        "Newspaper Zombie",
        "Screen Door Zombie",
        "Football Zombie",
        "Dancing Zombie",
        "Backup Dancer",
        "Ducky Tube Zombie",
        "Snorkel Zombie",
        "Zomboni",
        "Bobsled Team",
        "Dolphin Rider Zombie",
        "Jack-in-the-Box Zombie",
        "Balloon Zombie",
        "Digger Zombie",
        "Pogo Zombie",
        "Zombie Yeti",
        "Bungee Zombie",
        "Ladder Zombie",
        "Catapult Zombie",
        "Gargantuar",
        "Imp",
        "Dr. Zomboss",
        "Conehead Ducky Tube Zombie",
        "Buckethead Ducky Tube Zombie",
        "ZomBotany Peashooter Zombie",
        "ZomBotany Wall-nut Zombie",
        "ZomBotany Jalapeno Zombie",
        "ZomBotany Tall-nut Zombie",
        "ZomBotany Squash Zombie",
    ],
    "mini_games": [
        "ZomBotany",
        "Wall-nut Bowling",
        "Slot Machine",
        "It's Raining Seeds",
        "Beghouled",
        "Invisi-ghoul",
        "Seeing Stars",
        "Zombiquarium",
        "Beghouled Twist",
        "Big Trouble Little Zombie",
        "Portal Combat",
        "Column Like You See 'Em",
        "Bobsled Bonanza",
        "Zombie Nimble Zombie Quick",
        "Whack a Zombie",
        "Last Stand",
        "ZomBotany 2",
        "Wall-nut Bowling 2",
        "Pogo Party",
        "Dr. Zomboss's Revenge",
        "Buttered Popcorn",
        "Heavy Weapon",
        "Heat Wave",
        "BOMB All Together!",
        "Homerun Derby",
        "Air Raid",
        "Zombie Trap",
        "Vasebreaker",
    ],
}

WEB_LEVEL_ALIGNMENT_RAW = Path(
    "mods/pvz.base/assets/indexes/alignment/pvz1_levels_fandom_raw.json"
)

ZOMBIE_NAME_ALIASES = {
    "zombie": "basic",
    "drzomboss": "doctor_zomboss",
    "drzombosszombie": "doctor_zomboss",
    "zombotanywallnutzombie": "zombotany_wallnut",
    "zombotanytallnutzombie": "zombotany_tallnut",
}


def normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def load_names(category: str) -> List[str]:
    names: List[str] = []
    for path in sorted(glob.glob(f"mods/pvz.base/content/{category}/*.json")):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        names.append(data.get("name", data["id"]))
    return names


def diff_names(canonical: Iterable[str], current: Iterable[str]) -> Dict[str, List[str]]:
    canonical_map = {normalize(name): name for name in canonical}
    current_map = {normalize(name): name for name in current}
    missing = [canonical_map[key] for key in canonical_map if key not in current_map]
    extra = [current_map[key] for key in current_map if key not in canonical_map]
    return {"missing": missing, "extra": extra}


def zombie_name_lookup() -> Dict[str, str]:
    lookup: Dict[str, str] = dict(ZOMBIE_NAME_ALIASES)
    for path in sorted(glob.glob("mods/pvz.base/content/zombies/*.json")):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        lookup[normalize(data.get("name", data["id"]))] = data["id"]
    return lookup


def web_alignment_quality(level_by_id: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    if not WEB_LEVEL_ALIGNMENT_RAW.exists():
        return {"has_web_alignment_raw": False}

    with WEB_LEVEL_ALIGNMENT_RAW.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)

    lookup = zombie_name_lookup()
    entries = raw.get("levels", [])
    flag_mismatches: List[str] = []
    zombie_pool_mismatches: List[str] = []
    levels_with_web_pool = 0
    levels_without_web_pool = 0

    for entry in entries:
        level_id = entry.get("level_id")
        if level_id not in level_by_id:
            continue
        level = level_by_id[level_id]

        flags_count = entry.get("flags_count")
        if isinstance(flags_count, int) and level.get("flags_count") != flags_count:
            flag_mismatches.append(level_id)

        expected_pool = []
        for zombie_name in entry.get("first_play_zombies", []):
            zombie_id = lookup.get(normalize(zombie_name))
            if zombie_id is None:
                continue
            fqid = f"pvz.base:zombies:{zombie_id}"
            if fqid not in expected_pool:
                expected_pool.append(fqid)

        if expected_pool:
            levels_with_web_pool += 1
            current_pool = level.get("zombie_pool", [])
            if set(current_pool) != set(expected_pool):
                zombie_pool_mismatches.append(level_id)
        else:
            levels_without_web_pool += 1

    return {
        "has_web_alignment_raw": True,
        "web_alignment_levels": len(entries),
        "web_flag_mismatches": sorted(flag_mismatches),
        "web_zombie_pool_mismatches": sorted(zombie_pool_mismatches),
        "levels_with_web_pool": levels_with_web_pool,
        "levels_without_web_pool": levels_without_web_pool,
    }


def level_quality() -> Dict[str, int]:
    levels = []
    for path in sorted(glob.glob("mods/pvz.base/content/levels/*.json")):
        with open(path, "r", encoding="utf-8") as fh:
            levels.append(json.load(fh))
    return {
        "total_levels": len(levels),
        "levels_with_zomboss": sum(
            1
            for level in levels
            if any(
                wave.get("zombie_id", "").endswith(":doctor_zomboss")
                for wave in level.get("waves", [])
            )
        ),
        "levels_with_scripted_events": sum(1 for level in levels if level.get("scripted_events")),
        "levels_with_rewards": sum(1 for level in levels if "reward" in level),
    }


def level_alignment_quality() -> Dict[str, object]:
    levels = []
    for path in sorted(glob.glob("mods/pvz.base/content/levels/*.json")):
        with open(path, "r", encoding="utf-8") as fh:
            levels.append(json.load(fh))

    level_by_id = {level["id"]: level for level in levels}
    minigame_levels = sorted(level["id"] for level in levels if level.get("special_type") == "minigame")
    conveyor_levels = sorted(level["id"] for level in levels if level.get("conveyor_belt"))
    boss_levels = sorted(level["id"] for level in levels if level.get("special_type") == "boss")

    wave_files = {
        Path(path).stem
        for path in glob.glob("mods/pvz.base/content/waves/*.json")
    }
    missing_wave_defs = sorted(
        f"{level['id']}_flag" for level in levels if f"{level['id']}_flag" not in wave_files
    )
    extra_wave_defs = sorted(
        wave_id for wave_id in wave_files if not wave_id.endswith("_flag") or wave_id[:-5] not in level_by_id
    )

    tutorial = level_by_id.get("day_1", {})

    # Strategy Guide canonical flag counts (world-level notation 1-1..5-10).
    canonical_flags = {
        "day_1": 0,
        "day_2": 1,
        "day_3": 1,
        "day_4": 1,
        "day_5": 1,
        "day_6": 1,
        "day_7": 2,
        "day_8": 1,
        "day_9": 2,
        "day_10": 2,
        "night_1": 1,
        "night_2": 2,
        "night_3": 1,
        "night_4": 2,
        "night_5": 0,
        "night_6": 1,
        "night_7": 2,
        "night_8": 1,
        "night_9": 2,
        "night_10": 2,
        "pool_1": 1,
        "pool_2": 2,
        "pool_3": 2,
        "pool_4": 3,
        "pool_5": 2,
        "pool_6": 2,
        "pool_7": 3,
        "pool_8": 2,
        "pool_9": 3,
        "pool_10": 3,
        "fog_1": 1,
        "fog_2": 2,
        "fog_3": 1,
        "fog_4": 2,
        "fog_5": 0,
        "fog_6": 1,
        "fog_7": 2,
        "fog_8": 1,
        "fog_9": 2,
        "fog_10": 2,
        "roof_1": 1,
        "roof_2": 2,
        "roof_3": 2,
        "roof_4": 3,
        "roof_5": 2,
        "roof_6": 2,
        "roof_7": 3,
        "roof_8": 2,
        "roof_9": 3,
        "roof_10": 0,
    }
    flag_mismatches = sorted(
        level_id
        for level_id, expected in canonical_flags.items()
        if level_by_id.get(level_id, {}).get("flags_count") != expected
    )

    fog_5 = level_by_id.get("fog_5", {})
    roof_10 = level_by_id.get("roof_10", {})
    web_quality = web_alignment_quality(level_by_id)
    return {
        "tutorial_day_1_lawns": tutorial.get("lawns"),
        "tutorial_day_1_special_type": tutorial.get("special_type"),
        "fog_5_area_override": fog_5.get("area_override"),
        "roof_10_area_override": roof_10.get("area_override"),
        "minigame_levels": minigame_levels,
        "conveyor_levels": conveyor_levels,
        "boss_levels": boss_levels,
        "flag_mismatches": flag_mismatches,
        "levels_with_zombie_pool": sum(1 for level in levels if level.get("zombie_pool")),
        "levels_with_flags_count": sum(1 for level in levels if isinstance(level.get("flags_count"), int)),
        "missing_wave_defs": missing_wave_defs,
        "extra_wave_defs": extra_wave_defs,
        **web_quality,
    }


def animation_quality() -> Dict[str, object]:
    expected_targets: Set[str] = set()
    for category in ("plants", "zombies"):
        for path in sorted(glob.glob(f"mods/pvz.base/content/{category}/*.json")):
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            expected_targets.add(f"pvz.base:{category}:{data['id']}")

    covered: Set[str] = set()
    for path in sorted(glob.glob("mods/pvz.base/content/animation_configs/*.json")):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        covered.add(data.get("target_id", ""))

    missing = sorted(target for target in expected_targets if target not in covered)
    return {
        "expected_targets": len(expected_targets),
        "covered_targets": len(covered),
        "missing_targets": missing,
    }


def media_quality() -> Dict[str, object]:
    raw_path = Path("mods/pvz.base/assets/indexes/media/pvz_web_media_precise_raw.json")
    if not raw_path.exists():
        return {"has_precise_media_raw": False}
    with raw_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    targets = data.get("targets", [])
    missing_texture = sorted(
        target["target_id"]
        for target in targets
        if not target.get("texture_links")
    )
    totals = data.get("totals", {})
    return {
        "has_precise_media_raw": True,
        "targets_scanned": len(targets),
        "unique_textures": totals.get("unique_textures"),
        "unique_sound_file_pages": totals.get("unique_sound_file_pages"),
        "unique_direct_sound_urls": totals.get("unique_direct_sound_urls"),
        "targets_without_textures": missing_texture,
    }


def upgrade_quality() -> Dict[str, object]:
    plants = []
    for path in sorted(glob.glob("mods/pvz.base/content/plants/*.json")):
        with open(path, "r", encoding="utf-8") as fh:
            plants.append(json.load(fh))
    tagged = [plant["id"] for plant in plants if "upgrade" in plant.get("tags", [])]
    with_block = [plant["id"] for plant in plants if plant.get("upgrade")]
    missing_block = sorted(
        plant["id"]
        for plant in plants
        if "upgrade" in plant.get("tags", []) and not plant.get("upgrade")
    )
    invalid_block = sorted(
        plant["id"]
        for plant in plants
        if plant.get("upgrade") and (not plant["upgrade"].get("from") or plant["upgrade"].get("consume", 0) < 1)
    )
    return {
        "upgrade_tagged": sorted(tagged),
        "upgrade_with_block": sorted(with_block),
        "upgrade_missing_block": missing_block,
        "upgrade_invalid_block": invalid_block,
    }


def build_report() -> Dict[str, object]:
    report: Dict[str, object] = {"coverage": {}, "quality": {}}
    for category in ("plants", "zombies", "mini_games"):
        current = load_names(category)
        report["coverage"][category] = {
            "current_count": len(current),
            "canonical_count": len(CANONICAL[category]),
            **diff_names(CANONICAL[category], current),
        }
    report["quality"]["levels"] = level_quality()
    report["quality"]["level_alignment"] = level_alignment_quality()
    report["quality"]["animation"] = animation_quality()
    report["quality"]["media"] = media_quality()
    report["quality"]["upgrades"] = upgrade_quality()
    return report


def print_report(report: Dict[str, object]) -> None:
    for category in ("plants", "zombies", "mini_games"):
        data = report["coverage"][category]
        print(f"{category}: {data['current_count']}/{data['canonical_count']}")
        print(f"  missing ({len(data['missing'])}): {data['missing']}")
        print(f"  extra ({len(data['extra'])}): {data['extra']}")
    levels = report["quality"]["levels"]
    print("levels quality:")
    print(f"  total: {levels['total_levels']}")
    print(f"  with zomboss: {levels['levels_with_zomboss']}")
    print(f"  with scripted_events: {levels['levels_with_scripted_events']}")
    print(f"  with rewards: {levels['levels_with_rewards']}")
    lvl_align = report["quality"]["level_alignment"]
    print("level alignment:")
    print(f"  day_1 lawns/special: {lvl_align['tutorial_day_1_lawns']}/{lvl_align['tutorial_day_1_special_type']}")
    print(f"  fog_5 area_override: {lvl_align['fog_5_area_override']}")
    print(f"  roof_10 area_override: {lvl_align['roof_10_area_override']}")
    print(f"  minigame levels ({len(lvl_align['minigame_levels'])}): {lvl_align['minigame_levels']}")
    print(f"  conveyor levels ({len(lvl_align['conveyor_levels'])}): {lvl_align['conveyor_levels']}")
    print(f"  boss levels ({len(lvl_align['boss_levels'])}): {lvl_align['boss_levels']}")
    print(f"  canonical flag mismatches ({len(lvl_align['flag_mismatches'])}): {lvl_align['flag_mismatches']}")
    print(
        f"  zombie_pool+flags_count coverage: {lvl_align['levels_with_zombie_pool']}/"
        f"{lvl_align['levels_with_flags_count']}"
    )
    print(f"  missing wave defs ({len(lvl_align['missing_wave_defs'])}): {lvl_align['missing_wave_defs']}")
    print(f"  extra wave defs ({len(lvl_align['extra_wave_defs'])}): {lvl_align['extra_wave_defs']}")
    print(f"  web alignment raw: {lvl_align.get('has_web_alignment_raw')}")
    if lvl_align.get("has_web_alignment_raw"):
        print(
            f"  web pool coverage: {lvl_align['levels_with_web_pool']}/"
            f"{lvl_align['web_alignment_levels']}"
        )
        print(
            f"  web flag mismatches ({len(lvl_align['web_flag_mismatches'])}): "
            f"{lvl_align['web_flag_mismatches']}"
        )
        print(
            f"  web zombie_pool mismatches ({len(lvl_align['web_zombie_pool_mismatches'])}): "
            f"{lvl_align['web_zombie_pool_mismatches']}"
        )
    animation = report["quality"]["animation"]
    print("animation quality:")
    print(f"  covered: {animation['covered_targets']}/{animation['expected_targets']}")
    print(f"  missing targets ({len(animation['missing_targets'])}): {animation['missing_targets']}")
    media = report["quality"]["media"]
    print("media quality:")
    print(f"  has precise raw: {media.get('has_precise_media_raw')}")
    if media.get("has_precise_media_raw"):
        print(f"  targets scanned: {media['targets_scanned']}")
        print(f"  unique textures: {media['unique_textures']}")
        print(f"  unique sound file pages: {media['unique_sound_file_pages']}")
        print(f"  unique direct sound urls: {media['unique_direct_sound_urls']}")
        print(
            f"  targets without textures ({len(media['targets_without_textures'])}): "
            f"{media['targets_without_textures']}"
        )
    upgrades = report["quality"]["upgrades"]
    print("upgrade quality:")
    print(
        f"  tagged/with_block: {len(upgrades['upgrade_tagged'])}/"
        f"{len(upgrades['upgrade_with_block'])}"
    )
    print(
        f"  missing block ({len(upgrades['upgrade_missing_block'])}): "
        f"{upgrades['upgrade_missing_block']}"
    )
    print(
        f"  invalid block ({len(upgrades['upgrade_invalid_block'])}): "
        f"{upgrades['upgrade_invalid_block']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare pvz.base with canonical PvZ1 content.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2))
        return
    print_report(report)


if __name__ == "__main__":
    main()
