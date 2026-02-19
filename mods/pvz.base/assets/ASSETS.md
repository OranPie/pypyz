# pvz.base Assets Layout

- `sprites/`: local sprite sheets/textures (optional, can be empty).
- `audio/`: local sound files (optional, can be empty).
- `indexes/media/`: generated media crawl snapshots used by `media_resources.raw_snapshot`.

Validation rules:

- Local asset references in content must use `assets/...` paths.
- Referenced local asset files must exist.
- External `http(s)` URLs are allowed for web-indexed references.
