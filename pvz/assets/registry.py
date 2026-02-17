from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class AssetHandler(Protocol):
    def can_handle(self, path: Path) -> bool:
        ...

    def load(self, data: bytes, *, path: Path) -> Any:
        ...


@dataclass
class BuiltinJSONHandler:
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".json"

    def load(self, data: bytes, *, path: Path) -> Any:
        return json.loads(data.decode("utf-8"))


class AssetRegistry:
    def __init__(self) -> None:
        self._handlers: list[AssetHandler] = []

    def register(self, handler: AssetHandler) -> None:
        self._handlers.append(handler)

    def load_path(self, path: Path) -> Any:
        raw = path.read_bytes()
        for handler in self._handlers:
            if handler.can_handle(path):
                return handler.load(raw, path=path)
        return raw
