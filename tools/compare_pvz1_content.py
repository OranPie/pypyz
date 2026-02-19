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
    raw_path = Path("mods/pvz.base/assets/web_resources/pvz_web_media_precise_raw.json")
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
