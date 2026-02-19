from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

import requests

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
BASE_WIKI = "https://plantsvszombies.fandom.com/wiki/"

TEXTURE_RE = re.compile(
    r"https://static\.wikia\.nocookie\.net/[^\s\"<>]+?\.(?:png|jpg|jpeg|webp)",
    re.IGNORECASE,
)
SOUND_FILE_PAGE_RE = re.compile(
    r"https://plantsvszombies\.fandom\.com/wiki/File:[^\s\"<>]+?\.(?:ogg|mp3|wav)",
    re.IGNORECASE,
)
FILE_HREF_RE = re.compile(r"href=\"(/wiki/File:[^\"]+)\"")
DIRECT_SOUND_RE = re.compile(
    r"https://static\.wikia\.nocookie\.net/[^\s\"<>]+?\.(?:ogg|mp3|wav)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Target:
    target_id: str
    name: str
    category: str


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fetch(url: str) -> tuple[int, str]:
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": USER_AGENT},
    )
    return response.status_code, response.text


def _canonicalize_url(url: str) -> str:
    url = unquote(url)
    if "?" in url:
        url = url.split("?", 1)[0]
    return url


def _slug_from_name(name: str) -> str:
    return name.replace(" ", "_")


def _slug_from_id(item_id: str) -> str:
    return item_id.replace("_", " ").title().replace(" ", "_")


def _candidate_page_urls(target: Target) -> list[str]:
    custom = {
        "wallnut": "Wall-nut",
        "tall_nut": "Tall-nut",
        "threepeater": "Threepeater",
        "tangle_kelp": "Tangle_Kelp",
        "sun_shroom": "Sun-shroom",
        "fume_shroom": "Fume-shroom",
        "puff_shroom": "Puff-shroom",
        "hypno_shroom": "Hypno-shroom",
        "ice_shroom": "Ice-shroom",
        "magnet_shroom": "Magnet-shroom",
        "gloom_shroom": "Gloom-shroom",
        "wallnut_bowling": "Wall-nut_Bowling",
        "basic": "Zombie",
        "conehead_ducky": "Conehead_Ducky_Tube_Zombie",
        "buckethead_ducky": "Buckethead_Ducky_Tube_Zombie",
        "zombotany_peashooter": "Peashooter_Zombie",
        "zombotany_wallnut": "Wall-nut_Zombie",
        "zombotany_jalapeno": "Jalapeño_Zombie",
        "zombotany_tallnut": "Tall-nut_Zombie",
        "zombotany_squash": "Squash_Zombie",
    }

    local_id = target.target_id.rsplit(":", 1)[-1]
    slugs = [_slug_from_name(target.name)]
    if local_id in custom:
        slugs.append(custom[local_id])
    slugs.extend([local_id, _slug_from_id(local_id)])

    uniq: list[str] = []
    for slug in slugs:
        if slug not in uniq:
            uniq.append(slug)
    return [BASE_WIKI + slug for slug in uniq]


def _load_targets(content_root: Path) -> list[Target]:
    targets: list[Target] = []
    for category in ("plants", "zombies"):
        for path in sorted((content_root / category).glob("*.json")):
            data = _read_json(path)
            local_id = str(data["id"])
            full_id = f"pvz.base:{category}:{local_id}"
            targets.append(Target(target_id=full_id, name=str(data["name"]), category=category))
    return targets


def _extract_texture_links(html: str) -> list[str]:
    return sorted({_canonicalize_url(url) for url in TEXTURE_RE.findall(html)})


def _extract_sound_file_pages(html: str) -> list[str]:
    links = {_canonicalize_url(url) for url in SOUND_FILE_PAGE_RE.findall(html)}
    for rel in FILE_HREF_RE.findall(html):
        full = "https://plantsvszombies.fandom.com" + rel
        if re.search(r"\.(ogg|mp3|wav)$", full, re.IGNORECASE):
            links.add(_canonicalize_url(full))
    return sorted(links)


def _resolve_sound_media_urls(file_pages: list[str]) -> tuple[dict[str, list[str]], set[str]]:
    resolved: dict[str, list[str]] = {}
    all_direct: set[str] = set()

    for url in file_pages:
        try:
            status, html = _fetch(url)
            if status != 200:
                continue
            direct = sorted({_canonicalize_url(u) for u in DIRECT_SOUND_RE.findall(html)})
            if direct:
                resolved[url] = direct
                all_direct.update(direct)
        except Exception:
            continue

    return resolved, all_direct


def gather_precise() -> dict:
    content_root = Path("mods/pvz.base/content")
    targets = _load_targets(content_root)

    target_rows: list[dict] = []
    all_textures: set[str] = set()
    all_sound_file_pages: set[str] = set()

    for target in targets:
        row = {
            "target_id": target.target_id,
            "name": target.name,
            "category": target.category,
            "source_page": None,
            "texture_links": [],
            "sound_file_pages": [],
            "errors": [],
        }

        for url in _candidate_page_urls(target):
            try:
                status, html = _fetch(url)
                if status != 200:
                    continue

                textures = _extract_texture_links(html)
                sound_pages = _extract_sound_file_pages(html)

                row["source_page"] = url
                row["texture_links"] = textures
                row["sound_file_pages"] = sound_pages
                all_textures.update(textures)
                all_sound_file_pages.update(sound_pages)
                break
            except Exception as exc:  # noqa: BLE001
                row["errors"].append(f"{url}: {exc}")

        target_rows.append(row)

    resolved_sounds, all_direct_sounds = _resolve_sound_media_urls(sorted(all_sound_file_pages))

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "method": "python.requests + web.run seed hubs",
        "targets_scanned": len(target_rows),
        "targets": target_rows,
        "totals": {
            "unique_textures": len(all_textures),
            "unique_sound_file_pages": len(all_sound_file_pages),
            "unique_direct_sound_urls": len(all_direct_sounds),
        },
        "texture_links": sorted(all_textures),
        "sound_file_pages": sorted(all_sound_file_pages),
        "direct_sound_urls": sorted(all_direct_sounds),
        "resolved_sound_map": resolved_sounds,
    }


def build_mod_files(payload: dict) -> None:
    content_root = Path("mods/pvz.base/content")
    assets_root = Path("mods/pvz.base/assets/web_resources")
    assets_root.mkdir(parents=True, exist_ok=True)
    (content_root / "media_resources").mkdir(parents=True, exist_ok=True)
    (content_root / "animation_configs").mkdir(parents=True, exist_ok=True)

    raw_path = assets_root / "pvz_web_media_precise_raw.json"
    raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    media_index = {
        "id": "pvz_web_media_precise_index",
        "source": "fandom+web.run+python.requests",
        "crawled_at": payload.get("generated_at_utc", ""),
        "page_sources": sorted(
            {
                row["source_page"]
                for row in payload.get("targets", [])
                if row.get("source_page")
            }
        ),
        "textures": payload.get("texture_links", []),
        "sounds": payload.get("direct_sound_urls", []),
        "notes": "Precise per-target scrape. Verify licensing before packaging assets.",
        "raw_snapshot": str(raw_path.relative_to(Path("mods/pvz.base"))),
    }

    (content_root / "media_resources" / "pvz_web_media_precise_index.json").write_text(
        json.dumps(media_index, indent=2),
        encoding="utf-8",
    )

    def pick_frames(target_row: dict, limit: int = 4) -> list[str]:
        links = target_row.get("texture_links", [])
        return links[:limit]

    for row in payload.get("targets", []):
        target_id = row.get("target_id", "")
        if not target_id:
            continue
        frames = pick_frames(row)
        if not frames:
            continue

        local_id = target_id.rsplit(":", 1)[-1]
        category = target_id.split(":")[1]
        anim_id = f"{local_id}_{'walk' if category == 'zombies' else 'idle'}"
        anim_path = content_root / "animation_configs" / f"{anim_id}.json"

        frame_entries = [
            {
                "frame": idx,
                "texture": texture,
                "duration_ms": 83 if category == "plants" else 100,
            }
            for idx, texture in enumerate(frames)
        ]

        sound_events: list[dict] = []
        if category == "zombies" and payload.get("direct_sound_urls"):
            for sound in payload["direct_sound_urls"]:
                name = sound.lower()
                if "groan" in name or "zombiebite" in name:
                    event = "step" if "groan" in name else "attack"
                    sound_events.append({"event": event, "sound_url": sound})
            if not sound_events:
                sound_events = [
                    {
                        "event": "step",
                        "sound_url": payload["direct_sound_urls"][0],
                    }
                ]

        anim_payload = {
            "id": anim_id,
            "target_id": target_id,
            "fps": 12 if category == "plants" else 10,
            "loop": True,
            "frames": frame_entries,
            "sound_events": sound_events[:2],
        }

        anim_path.write_text(json.dumps(anim_payload, indent=2), encoding="utf-8")


def main() -> int:
    payload = gather_precise()
    out_dir = Path("data/web_resources")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pvz_media_resources_precise.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    build_mod_files(payload)

    print(f"Saved: {out_path}")
    print(f"Targets scanned: {payload['targets_scanned']}")
    print(f"Unique textures: {payload['totals']['unique_textures']}")
    print(f"Unique direct sounds: {payload['totals']['unique_direct_sound_urls']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
