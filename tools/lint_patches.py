from __future__ import annotations

import argparse
from pathlib import Path

from pvz.content.loader import ModLoader


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply all mod patches in-memory to validate them")
    parser.add_argument("mods_dir", type=Path)
    parser.add_argument("--schemas", type=Path, default=Path("schemas"))
    args = parser.parse_args()

    loader = ModLoader(args.mods_dir, schema_root=args.schemas)
    loaded = loader.load()

    patch_count = 0
    for mod in loaded.mods:
        patch_root = mod.path / "patches"
        if not patch_root.exists():
            continue
        patch_count += len(list(patch_root.rglob("*.json")))

    print(f"OK: {patch_count} patch file(s) validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
