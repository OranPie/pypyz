from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

import requests


USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


@dataclass(frozen=True)
class SourcePage:
    url: str
    kind: str


SOURCE_PAGES: tuple[SourcePage, ...] = (
    SourcePage("https://plantsvszombies.fandom.com/wiki/Peashooter", "plant"),
    SourcePage("https://plantsvszombies.fandom.com/wiki/Sunflower", "plant"),
    SourcePage("https://plantsvszombies.fandom.com/wiki/Wall-nut", "plant"),
    SourcePage("https://plantsvszombies.fandom.com/wiki/Cherry_Bomb", "plant"),
    SourcePage("https://plantsvszombies.fandom.com/wiki/Zombie", "zombie"),
    SourcePage("https://plantsvszombies.fandom.com/wiki/Conehead_Zombie", "zombie"),
    SourcePage("https://plantsvszombies.fandom.com/wiki/Lawn_Mower", "system"),
    SourcePage("https://plantsvszombies.fandom.com/wiki/Sun", "system"),
)

# Collected with web.run search for texture/sound resource hubs.
WEB_RUN_RESOURCE_HUBS: tuple[str, ...] = (
    "https://plantsvszombies.wiki.gg/wiki/Category:Plants_vs._Zombies_Images",
    "https://plantsvszombies.wiki.gg/wiki/Category:Plants_vs._Zombies_Audio",
    "https://plantsvszombies.fandom.com/wiki/Pea",
)

SOUND_LINK_RE = re.compile(
    r"https://plantsvszombies\.fandom\.com/wiki/File:[^\s\"<>]+?\.(?:ogg|mp3|wav)",
    re.IGNORECASE,
)
TEXTURE_LINK_RE = re.compile(
    r"https://static\.wikia\.nocookie\.net/[^\s\"<>]+?\.(?:png|jpg|jpeg|webp)",
    re.IGNORECASE,
)


def _fetch_html(url: str) -> str:
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return response.text


def _extract_links(html: str, pattern: re.Pattern[str]) -> list[str]:
    return sorted(set(pattern.findall(html)))


def _best_sample(links: Iterable[str], size: int = 8) -> list[str]:
    return sorted(links)[:size]


def gather() -> dict:
    page_rows: list[dict] = []
    all_texture_links: set[str] = set()
    all_sound_links: set[str] = set()

    for page in SOURCE_PAGES:
        try:
            html = _fetch_html(page.url)
            texture_links = _extract_links(html, TEXTURE_LINK_RE)
            sound_links = _extract_links(html, SOUND_LINK_RE)
            all_texture_links.update(texture_links)
            all_sound_links.update(sound_links)
            page_rows.append(
                {
                    "url": page.url,
                    "kind": page.kind,
                    "texture_count": len(texture_links),
                    "sound_count": len(sound_links),
                    "texture_samples": _best_sample(texture_links),
                    "sound_samples": _best_sample(sound_links),
                }
            )
        except Exception as exc:  # noqa: BLE001
            page_rows.append(
                {
                    "url": page.url,
                    "kind": page.kind,
                    "error": str(exc),
                }
            )

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "resource_hubs_from_web_run": list(WEB_RUN_RESOURCE_HUBS),
        "source_pages": page_rows,
        "totals": {
            "texture_links_unique": len(all_texture_links),
            "sound_links_unique": len(all_sound_links),
        },
        "texture_links": sorted(all_texture_links),
        "sound_links": sorted(all_sound_links),
        "texture_link_samples": _best_sample(all_texture_links, size=30),
        "sound_link_samples": _best_sample(all_sound_links, size=30),
    }


def main() -> int:
    output = gather()

    out_dir = Path("data/web_resources")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pvz_media_resources.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"Saved: {out_path}")
    print(f"Unique texture links: {output['totals']['texture_links_unique']}")
    print(f"Unique sound links: {output['totals']['sound_links_unique']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
