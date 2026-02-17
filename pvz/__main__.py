from __future__ import annotations

import argparse
import json
from pathlib import Path

from pvz.combat import BattleState, simulate_wave
from pvz.game import GameBootstrap
from pvz.modes import CampaignService, ShopService, build_almanac
from pvz.scripting import HookContext, ScriptManager


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mod-driven PvZ-like prototype")
    parser.add_argument("--mods", type=Path, default=Path("mods"), help="mods directory")
    parser.add_argument("--schemas", type=Path, default=Path("schemas"), help="schema directory")
    parser.add_argument(
        "--save", type=Path, default=Path("saves/profile.json"), help="save file path"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="only validate and resolve content, do not initialize services",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="run a tiny combat simulation from loaded definitions",
    )
    return parser


def _pick_first(category: dict[str, dict]) -> dict | None:
    if not category:
        return None
    return next(iter(category.values())).data


def main() -> int:
    args = _parser().parse_args()
    bootstrap = GameBootstrap(mods_dir=args.mods, schemas_dir=args.schemas, save_path=args.save)

    loaded = bootstrap.load_content()
    print(f"Loaded mods: {', '.join(loaded.mod_ids)}")
    print(f"Content categories: {', '.join(sorted(loaded.registry.categories.keys()))}")

    script_manager = ScriptManager()
    script_manager.load_from_mods(loaded.mods)
    script_manager.run_hook("on_startup", context=HookContext(tick=0, payload={"phase": "startup"}))

    if args.validate_only:
        return 0

    store = bootstrap.ensure_save()
    save = store.load()
    campaign = CampaignService(loaded.registry)
    shop = ShopService(loaded.registry)

    current_level = campaign.get_current_level(save)
    print(f"Current level: {current_level['id']}")
    print(f"Shop items: {len(shop.list_items())}")
    print(f"Almanac entries: {len(build_almanac(loaded.registry))}")

    if args.simulate:
        plant = _pick_first(loaded.registry.categories.get("plants", {}))
        zombie = _pick_first(loaded.registry.categories.get("zombies", {}))
        state = BattleState(
            sun=int(current_level.get("sun_start", 50)),
            lawns=int(current_level.get("lawns", 5)),
            active_plants=[{"damage": int((plant or {}).get("damage", 0))}],
            active_zombies=[
                {
                    "hp": int((zombie or {}).get("max_hp", 30)),
                    "drain_sun": 0,
                }
            ],
        )
        result = simulate_wave(state, duration_ticks=10)
        print("Sim result:", json.dumps(result, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
