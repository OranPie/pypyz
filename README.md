# pvz-mod-engine

Python prototype for a mod-driven PvZ-like game.

- Required base mod: `pvz.base`
- Primary content format: JSON
- Complex behavior: restricted Python hook scripts

## Run

```bash
python3 -m pvz --mods mods --schemas schemas --validate-only
python3 -m pvz --mods mods --schemas schemas --simulate
```

## Tooling

```bash
python3 -m tools.validate_mod mods/pvz.base --schemas schemas
python3 -m tools.resolve_load_order mods --schemas schemas
python3 -m tools.lint_patches mods --schemas schemas
python3 -m tools.dump_registry mods --schemas schemas
python3 tools/compare_pvz1_content.py
```

See `docs/mod_spec.md` for the full v1 folder format and schema surface.
