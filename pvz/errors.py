"""Domain errors for mod loading and runtime."""


class PvzError(Exception):
    """Base error for the project."""


class ManifestError(PvzError):
    """Raised when mod manifest is malformed."""


class SchemaValidationError(PvzError):
    """Raised when JSON content fails schema validation."""


class DependencyError(PvzError):
    """Raised when dependency constraints cannot be resolved."""


class MissingBaseModError(PvzError):
    """Raised when required `pvz.base` mod is missing."""


class PatchError(PvzError):
    """Raised when a patch operation is invalid."""


class ScriptSecurityError(PvzError):
    """Raised when a script performs forbidden operations."""
