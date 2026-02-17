from __future__ import annotations

from dataclasses import dataclass

from pvz.models import ContentRegistry
from pvz.save.store import SaveModelV1


@dataclass
class CampaignService:
    registry: ContentRegistry

    def get_current_level(self, save: SaveModelV1) -> dict:
        level_id = save.campaign.get("node", "")
        if ":" not in level_id:
            level_id = f"pvz.base:levels:{level_id}"
        return self.registry.get("levels", level_id).data

    def mark_complete(self, save: SaveModelV1, level_id: str) -> None:
        completed = save.campaign.setdefault("completed", [])
        if level_id not in completed:
            completed.append(level_id)
