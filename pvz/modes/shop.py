from __future__ import annotations

from dataclasses import dataclass

from pvz.models import ContentRegistry
from pvz.save.store import SaveModelV1


@dataclass
class ShopService:
    registry: ContentRegistry

    def list_items(self) -> list[dict]:
        return [item.data for item in self.registry.categories.get("shop", {}).values()]

    def buy(self, save: SaveModelV1, item_id: str) -> None:
        item = self.registry.get("shop", item_id).data
        price = int(item.get("price", 0))
        coins = int(save.shop.get("coins", 0))
        if coins < price:
            raise ValueError("not enough coins")
        save.shop["coins"] = coins - price
        save.shop.setdefault("inventory", []).append(item_id)
