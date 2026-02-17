from __future__ import annotations

from dataclasses import dataclass

from pvz.models import ContentRegistry
from pvz.save.store import SaveModelV1


@dataclass
class ZenService:
    registry: ContentRegistry

    def tick(self, save: SaveModelV1, now_tick: int) -> None:
        last_tick = int(save.zen.get("last_tick", 0))
        elapsed = max(0, now_tick - last_tick)
        plants = save.zen.setdefault("plants", [])
        for plant in plants:
            plant["growth"] = min(100, int(plant.get("growth", 0)) + elapsed)
        save.zen["last_tick"] = now_tick
