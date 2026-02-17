from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pvz.content.loader import LoadedGameData, ModLoader
from pvz.modes import CampaignService, ShopService, ZenService
from pvz.save import SaveStore


@dataclass
class GameBootstrap:
    mods_dir: Path
    schemas_dir: Path
    save_path: Path

    def load_content(self) -> LoadedGameData:
        loader = ModLoader(self.mods_dir, schema_root=self.schemas_dir)
        return loader.load()

    def initialize_services(self) -> tuple[LoadedGameData, CampaignService, ShopService, ZenService]:
        data = self.load_content()
        campaign = CampaignService(data.registry)
        shop = ShopService(data.registry)
        zen = ZenService(data.registry)
        return data, campaign, shop, zen

    def ensure_save(self) -> SaveStore:
        store = SaveStore(self.save_path)
        save = store.load()
        store.save(save)
        return store
