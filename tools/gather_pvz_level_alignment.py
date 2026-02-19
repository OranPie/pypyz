#!/usr/bin/env python3
"""Gather PvZ1 adventure level alignment metadata from Fandom."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

WORLD_PREFIXES: List[Tuple[str, int]] = [
    ("day", 1),
    ("night", 2),
    ("pool", 3),
    ("fog", 4),
    ("roof", 5),
]

FLAG_WORDS = {
    "none": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}

NAME_ALIASES = {
    "Zombie": "Regular Zombie",
    "Dr Zomboss": "Dr. Zomboss",
}

IGNORED_TITLES = {"Adventure Mode"}


def parse_flag_count(flag_text: str) -> Optional[int]:
    lowered = flag_text.lower()
    for word, count in FLAG_WORDS.items():
        if re.search(rf"\b{word}\b", lowered):
            return count
    match = re.search(r"(\d+)", lowered)
    if match:
        return int(match.group(1))
    return None


def clean_title(title: str) -> str:
    value = title.strip()
    if value.endswith("(PvZ)"):
        value = value[:-5].strip()
    return NAME_ALIASES.get(value, value)


def parse_infobox(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    data: Dict[str, Optional[str]] = {
        "location": None,
        "type": None,
        "flags_text": None,
        "first_time_reward": None,
        "replay_reward": None,
    }
    infobox = soup.select_one("aside.portable-infobox")
    if not infobox:
        return data
    for item in infobox.select("div.pi-item.pi-data"):
        label = item.select_one("h3.pi-data-label")
        value = item.select_one("div.pi-data-value")
        if not label or not value:
            continue
        label_text = label.get_text(" ", strip=True).lower()
        value_text = " ".join(value.get_text(" ", strip=True).split())
        if label_text == "location":
            data["location"] = value_text
        elif label_text == "type":
            data["type"] = value_text
        elif label_text == "flags":
            data["flags_text"] = value_text
        elif label_text == "first time":
            data["first_time_reward"] = value_text
        elif label_text == "replaying":
            data["replay_reward"] = value_text
    return data


def parse_first_play_wave_zombies(soup: BeautifulSoup) -> List[str]:
    waves_heading = next(
        (heading for heading in soup.select("h2") if "Waves" in heading.get_text(" ", strip=True)),
        None,
    )
    if not waves_heading:
        return []

    zombies: List[str] = []
    sibling = waves_heading.find_next_sibling()
    while sibling and sibling.name != "h2":
        text = sibling.get_text(" ", strip=True)
        if sibling.name == "p" and "After finishing Adventure Mode once" in text:
            break
        if sibling.name == "table":
            for link in sibling.select("a[title]"):
                raw_title = link.get("title", "").strip()
                if not raw_title:
                    continue
                title = clean_title(raw_title)
                if not title or title in IGNORED_TITLES or title.startswith("Level ") or title.startswith("Category:"):
                    continue
                if title not in zombies:
                    zombies.append(title)
        sibling = sibling.find_next_sibling()
    return zombies


def gather(base_url: str, timeout: float) -> Dict[str, object]:
    session = requests.Session()
    levels: List[Dict[str, object]] = []
    for prefix, world in WORLD_PREFIXES:
        for stage in range(1, 11):
            level_id = f"{prefix}_{stage}"
            page = f"Level_{world}-{stage}"
            url = f"{base_url.rstrip('/')}/{page}"
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            infobox = parse_infobox(soup)
            flags_text = infobox.get("flags_text") or ""
            levels.append(
                {
                    "level_id": level_id,
                    "page": page,
                    "url": url,
                    "location": infobox.get("location"),
                    "type": infobox.get("type"),
                    "flags_text": flags_text,
                    "flags_count": parse_flag_count(flags_text) if flags_text else None,
                    "first_time_reward": infobox.get("first_time_reward"),
                    "replay_reward": infobox.get("replay_reward"),
                    "first_play_zombies": parse_first_play_wave_zombies(soup),
                }
            )

    return {
        "source": "plantsvszombies.fandom.com",
        "note": "Data is parsed from level infobox + first-play wave tables when present.",
        "levels": levels,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Gather PvZ1 level alignment metadata from Fandom.")
    parser.add_argument(
        "--out",
        default="mods/pvz.base/assets/indexes/alignment/pvz1_levels_fandom_raw.json",
        help="Output path for gathered JSON.",
    )
    parser.add_argument(
        "--base-url",
        default="https://plantsvszombies.fandom.com/wiki",
        help="Base URL for level pages.",
    )
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds.")
    args = parser.parse_args()

    report = gather(args.base_url, args.timeout)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({len(report['levels'])} levels)")


if __name__ == "__main__":
    main()
