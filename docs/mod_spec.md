# PvZ Mod Format Spec (v1)

## Startup contract
- Engine **must** load a valid `pvz.base` mod at startup.
- If `pvz.base` is missing or invalid, startup fails.
- Additional mods load after dependency resolution and may patch base content.

## Folder format

```text
<mod>/
  mod.json
  content/
    plants/*.json
    zombies/*.json
    projectiles/*.json
    status_effects/*.json
    levels/*.json
    waves/*.json
    map_nodes/*.json
    mini_games/*.json
    puzzle_levels/*.json
    survival_levels/*.json
    shop/*.json
    almanac/*.json
    zen/*.json
    unlock_rules/*.json
    achievements/*.json
    economy/*.json
    ui_screens/*.json
    audio_events/*.json
    media_resources/*.json
    animation_configs/*.json
  patches/*.json
  scripts/*.py
  assets/**
  localization/*.json
```

## Manifest (`mod.json`)
Required:
- `id`, `version`, `title`, `engine_api`

Optional:
- `requires`: dependency list `[{"id": "pvz.base", "version": "^1.0.0"}]`
- `conflicts`
- `load_before`, `load_after`
- `capabilities` (for script API permissions)
- `entrypoints` (hook scripts)

## IDs and references
- Local IDs are auto-expanded into `mod_id:category:id`.
- Cross-category references should always use fully qualified IDs.
- Examples:
  - `pvz.base:plants:peashooter`
  - `pvz.base:levels:day_1`

## Plant upgrade definition (v1)
- Plants may define `upgrade` metadata to describe replacement upgrades in a mod-driven way.
- `upgrade.from`: source plant IDs consumed by the upgrade.
- `upgrade.consume`: required count from `upgrade.from` (for example, Cob Cannon uses `2` Kernel-pults).
- `upgrade.placement`:
  - `same_tile` (replace the source plant in place)
  - `same_tile_requires_host` (upgrade in place while preserving host constraints, e.g. Lily Pad / shroom host rules)
  - `adjacent_pair` (requires adjacent sources; used by multi-tile upgrades)
- `upgrade.requires`: optional prerequisite IDs (unlock rules/shop grants/etc).
- `upgrade.inherit`: optional transfer behavior (`hp_ratio`, `statuses`, `cooldown_progress`).

## Patch format
Each `patches/*.json` file can be either:
- `[{...}, {...}]`
- `{ "ops": [{...}, {...}] }`

Patch operation fields:
- `target` (content item id)
- `op` in `add|replace|remove|merge|append`
- `path` JSON pointer (default `/`)
- `value` payload for op

## Script hooks and safety
- Hook functions are discovered by `on_` prefix (e.g. `on_startup`, `on_tick`).
- Scripts run with restricted builtins and allowlisted imports.
- Runtime API methods are capability-gated (`events.emit`, `state.write`, `combat.write`).

## v1 content surface (PvZ-style)
This v1 schema pack covers:
- Adventure campaign (`levels`, `waves`, `map_nodes`)
- Core entities (`plants`, `zombies`, `projectiles`, `status_effects`)
- Side modes (`mini_games`, `puzzle_levels`, `survival_levels`, `zen`)
- Meta/progression (`shop`, `unlock_rules`, `achievements`, `economy`)
- UX content (`almanac`, `ui_screens`, `audio_events`, `localization`)
- External media index + animation recognition (`media_resources`, `animation_configs`)

## Adventure level metadata notes
- `levels/*.json` may include `scripted_events` for timeline cues (music, huge wave, boss phases).
- `levels/*.json` may include `reward` metadata for stage clear payouts/cards/trophies.
- `roof_10` is expected to carry boss metadata via `doctor_zomboss` wave + scripted events.
