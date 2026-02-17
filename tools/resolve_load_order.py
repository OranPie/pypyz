from __future__ import annotations

import argparse
from pathlib import Path

from pvz.content.dependency import resolve_load_order
from pvz.content.loader import ModLoader


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve deterministic mod load order")
    parser.add_argument("mods_dir", type=Path)
    parser.add_argument("--schemas", type=Path, default=Path("schemas"))
    args = parser.parse_args()

    loader = ModLoader(args.mods_dir, schema_root=args.schemas)
    mod_map = loader.discover_mods()
    ordered = resolve_load_order(mod_map)
    for index, mod in enumerate(ordered, start=1):
        print(f"{index:02d}. {mod.manifest.id}@{mod.manifest.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
