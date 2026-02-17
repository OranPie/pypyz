# pvz-mod-engine

Python prototype for a mod-driven PvZ-like game. Core content is loaded from mods, with a required base mod id: `pvz.base`.

## Quick start

```bash
python -m pvz --mods mods --validate-only
python -m pvz --mods mods
```

## Tools

```bash
python -m tools.validate_mod mods/pvz.base
python -m tools.resolve_load_order mods
python -m tools.dump_registry mods
python -m tools.lint_patches mods
```
