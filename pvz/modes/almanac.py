from __future__ import annotations

from pvz.models import ContentRegistry


def build_almanac(registry: ContentRegistry) -> list[dict]:
    entries: list[dict] = []
    for item in registry.categories.get("almanac", {}).values():
        entries.append(item.data)
    return sorted(entries, key=lambda e: e.get("title", ""))
