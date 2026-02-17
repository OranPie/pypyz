from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Dependency:
    id: str
    version: str = ""


@dataclass(frozen=True)
class ModManifest:
    id: str
    version: str
    title: str
    engine_api: str
    requires: tuple[Dependency, ...] = ()
    conflicts: tuple[Dependency, ...] = ()
    load_before: tuple[str, ...] = ()
    load_after: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    entrypoints: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ModPackage:
    manifest: ModManifest
    path: Path


@dataclass
class ContentItem:
    id: str
    category: str
    data: dict[str, Any]
    source_mod: str
    source_path: Path


@dataclass
class ContentRegistry:
    categories: dict[str, dict[str, ContentItem]] = field(default_factory=dict)

    def add(self, item: ContentItem) -> None:
        bucket = self.categories.setdefault(item.category, {})
        if item.id in bucket:
            raise ValueError(f"duplicate content id: {item.id}")
        bucket[item.id] = item

    def get(self, category: str, item_id: str) -> ContentItem:
        return self.categories[category][item_id]

    def as_plain_data(self) -> dict[str, dict[str, dict[str, Any]]]:
        return {
            category: {item_id: item.data for item_id, item in entries.items()}
            for category, entries in self.categories.items()
        }
