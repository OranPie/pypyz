from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SaveModelV1:
    version: int = 1
    campaign: dict[str, Any] = field(default_factory=lambda: {"node": "day_1", "completed": []})
    unlocks: dict[str, Any] = field(default_factory=lambda: {"plants": ["pvz.base:plants:peashooter"]})
    shop: dict[str, Any] = field(default_factory=lambda: {"coins": 0, "inventory": []})
    zen: dict[str, Any] = field(default_factory=lambda: {"plants": [], "last_tick": 0})
    settings: dict[str, Any] = field(default_factory=lambda: {"volume": 100, "fullscreen": False})


class SaveStore:
    def __init__(self, save_path: Path) -> None:
        self.save_path = save_path

    def load(self) -> SaveModelV1:
        if not self.save_path.exists():
            return SaveModelV1()
        raw = json.loads(self.save_path.read_text(encoding="utf-8"))
        raw = self._migrate(raw)
        return SaveModelV1(**raw)

    def save(self, data: SaveModelV1) -> None:
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_path.write_text(
            json.dumps(asdict(data), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _migrate(self, payload: dict[str, Any]) -> dict[str, Any]:
        version = int(payload.get("version", 0))
        if version == 1:
            return payload

        if version == 0:
            migrated = SaveModelV1()
            merged = asdict(migrated)
            merged.update(payload)
            merged["version"] = 1
            return merged

        raise ValueError(f"unsupported save version: {version}")
