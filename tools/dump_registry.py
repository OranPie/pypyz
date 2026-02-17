from __future__ import annotations

import argparse
import json
from pathlib import Path

from pvz.content.loader import ModLoader


def main() -> int:
    parser = argparse.ArgumentParser(description="Dump fully resolved content registry")
    parser.add_argument("mods_dir", type=Path)
    parser.add_argument("--schemas", type=Path, default=Path("schemas"))
    args = parser.parse_args()

    loader = ModLoader(args.mods_dir, schema_root=args.schemas)
    loaded = loader.load()
    print(json.dumps(loaded.registry.as_plain_data(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
