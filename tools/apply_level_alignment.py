#!/usr/bin/env python3
"""Apply gathered PvZ1 level alignment metadata to pvz.base level definitions."""

from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path
from typing import Dict, List


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def build_zombie_lookup(mod_id: str, levels_dir: Path) -> Dict[str, str]:
    root = levels_dir.parent / "zombies"
    lookup: Dict[str, str] = {"zombie": "basic"}
    for path in sorted(glob.glob(str(root / "*.json"))):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        lookup[normalize_name(data.get("name", data["id"]))] = data["id"]
    lookup.update(
        {
            "drzomboss": "doctor_zomboss",
            "drzombosszombie": "doctor_zomboss",
            "zombotanywallnutzombie": "zombotany_wallnut",
            "zombotanytallnutzombie": "zombotany_tallnut",
        }
    )
    return lookup


def map_zombies(
    names: List[str],
    lookup: Dict[str, str],
    mod_id: str,
) -> List[str]:
    mapped: List[str] = []
    for name in names:
        zombie_id = lookup.get(normalize_name(name))
        if zombie_id is None:
            continue
        fqid = f"{mod_id}:zombies:{zombie_id}"
        if fqid not in mapped:
            mapped.append(fqid)
    return mapped


def apply_alignment(
    raw_path: Path,
    levels_dir: Path,
    mod_id: str,
    update_flags: bool,
) -> Dict[str, int]:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    by_level = {entry["level_id"]: entry for entry in raw.get("levels", [])}
    zombie_lookup = build_zombie_lookup(mod_id, levels_dir)

    updated = 0
    flags_updated = 0
    zombie_pool_updated = 0
    unmapped_levels = 0

    for path in sorted(glob.glob(str(levels_dir / "*.json"))):
        level_path = Path(path)
        level = json.loads(level_path.read_text(encoding="utf-8"))
        entry = by_level.get(level["id"])
        if not entry:
            continue

        changed = False
        if update_flags:
            flags_count = entry.get("flags_count")
            if isinstance(flags_count, int) and level.get("flags_count") != flags_count:
                level["flags_count"] = flags_count
                flags_updated += 1
                changed = True

        mapped_pool = map_zombies(entry.get("first_play_zombies", []), zombie_lookup, mod_id)
        # Keep existing pool for pages without a parseable first-play table.
        if mapped_pool:
            if level.get("zombie_pool") != mapped_pool:
                level["zombie_pool"] = mapped_pool
                zombie_pool_updated += 1
                changed = True
        else:
            unmapped_levels += 1

        if changed:
            level_path.write_text(json.dumps(level, indent=2) + "\n", encoding="utf-8")
            updated += 1

    return {
        "levels_updated": updated,
        "flags_updated": flags_updated,
        "zombie_pool_updated": zombie_pool_updated,
        "levels_without_mapped_pool": unmapped_levels,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply web gathered level alignment into pvz.base levels.")
    parser.add_argument(
        "--raw",
        default="mods/pvz.base/assets/indexes/alignment/pvz1_levels_fandom_raw.json",
        help="Path to gathered alignment JSON.",
    )
    parser.add_argument(
        "--levels-dir",
        default="mods/pvz.base/content/levels",
        help="Directory containing level JSON files.",
    )
    parser.add_argument(
        "--mod-id",
        default="pvz.base",
        help="Mod id used when writing fully-qualified zombie ids.",
    )
    parser.add_argument(
        "--no-flags",
        action="store_true",
        help="Do not update flags_count from raw data.",
    )
    args = parser.parse_args()

    summary = apply_alignment(
        raw_path=Path(args.raw),
        levels_dir=Path(args.levels_dir),
        mod_id=args.mod_id,
        update_flags=not args.no_flags,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
