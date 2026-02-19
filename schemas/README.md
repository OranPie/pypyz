# v1 Schema Catalog

Each top-level folder under `content/` maps to a schema file.

- `plants` -> `plant.schema.json`
- `zombies` -> `zombie.schema.json`
- `projectiles` -> `projectile.schema.json`
- `status_effects` -> `status_effect.schema.json`
- `levels` -> `level.schema.json`
- `waves` -> `wave.schema.json`
- `map_nodes` -> `map_node.schema.json`
- `mini_games` -> `minigame.schema.json`
- `puzzle_levels` -> `puzzle_level.schema.json`
- `survival_levels` -> `survival_level.schema.json`
- `shop` -> `shop_item.schema.json`
- `almanac` -> `almanac_entry.schema.json`
- `zen` -> `zen_item.schema.json`
- `unlock_rules` -> `unlock_rule.schema.json`
- `achievements` -> `achievement.schema.json`
- `economy` -> `economy.schema.json`
- `ui_screens` -> `ui_screen.schema.json`
- `audio_events` -> `audio_event.schema.json`
- `media_resources` -> `media_resource.schema.json`
- `animation_configs` -> `animation_config.schema.json`

`manifest.schema.json` validates `mod.json`.

Note: `plant.schema.json` includes optional `upgrade` metadata (`from`, `consume`, `placement`, `requires`, `inherit`) for explicit upgrade-path definitions.
