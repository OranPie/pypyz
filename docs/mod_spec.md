# Mod Specification (v1)

## Required base mod
- Engine startup hard-fails unless mod id `pvz.base` is present and valid.

## Mod layout

```text
<mod>/
  mod.json
  content/
    plants/*.json
    zombies/*.json
    levels/*.json
    shop/*.json
    almanac/*.json
    zen/*.json
  patches/*.json
  scripts/*.py
  assets/**
  localization/*.json
```

## `mod.json`
Required fields:
- `id`
- `version`
- `title`
- `engine_api`

Optional fields:
- `requires`/`conflicts`: array of `{ id, version }`
- `load_before`/`load_after`: array of mod ids
- `capabilities`: script capability list
- `entrypoints`: map name -> script path

## Content IDs
- If `id` is local (`peashooter`), engine expands to `mod_id:category:id`.
- Cross-mod references should use fully-qualified IDs.

## Patch format
`patches/*.json` can be:
- a list of patch ops, or
- `{ "ops": [...] }`

Patch operation fields:
- `target`: content id
- `op`: `add|replace|remove|merge|append`
- `path`: JSON pointer (default `/`)
- `value`: operation payload

## Script hooks
Functions named with `on_` prefix are registered. Current hooks include:
- `on_startup`
- `on_tick`

Scripts run in restricted runtime:
- limited builtins
- import allowlist (`math`, `random`)
- capability-gated API methods (`events.emit`, `state.write`, `combat.write`)
