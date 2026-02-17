"""Asset loader registry with pluggable handlers."""

from pvz.assets.registry import AssetHandler, AssetRegistry, BuiltinJSONHandler

__all__ = ["AssetHandler", "AssetRegistry", "BuiltinJSONHandler"]
