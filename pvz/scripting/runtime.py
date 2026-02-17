from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable

from pvz.errors import ScriptSecurityError


SAFE_BUILTINS = {
    "abs": abs,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "range": range,
    "round": round,
    "set": set,
    "str": str,
    "sum": sum,
    "tuple": tuple,
}


@dataclass
class HookContext:
    tick: int = 0
    entity_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class CapabilityAPI:
    def __init__(self, *, capabilities: set[str], state: dict[str, Any]) -> None:
        self._capabilities = capabilities
        self._state = state

    def _require(self, capability: str) -> None:
        if capability not in self._capabilities:
            raise ScriptSecurityError(f"capability denied: {capability}")

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        self._require("state.write")
        self._state[key] = value

    def emit_event(self, event: str, payload: dict[str, Any]) -> None:
        self._require("events.emit")
        events = self._state.setdefault("events", [])
        events.append({"event": event, "payload": payload})

    def apply_damage(self, target_id: str, amount: int) -> None:
        self._require("combat.write")
        damages = self._state.setdefault("damage", [])
        damages.append({"target": target_id, "amount": amount})


class HookRuntime:
    def __init__(self, *, allowed_imports: set[str] | None = None) -> None:
        self.allowed_imports = allowed_imports or {"math", "random"}
        self._hooks: dict[str, Callable[..., Any]] = {}

    def _restricted_import(
        self, name: str, globals_: Any = None, locals_: Any = None, fromlist: Any = (), level: int = 0
    ) -> Any:
        root = name.split(".", 1)[0]
        if root not in self.allowed_imports:
            raise ScriptSecurityError(f"import not allowed: {name}")
        return __import__(name, globals_, locals_, fromlist, level)

    def load_script(self, script_path: Path) -> None:
        code = script_path.read_text(encoding="utf-8")
        builtins_table = dict(SAFE_BUILTINS)
        builtins_table["__import__"] = self._restricted_import

        namespace: dict[str, Any] = {
            "__builtins__": MappingProxyType(builtins_table),
        }
        try:
            exec(compile(code, str(script_path), "exec"), namespace, namespace)
        except ScriptSecurityError:
            raise
        except Exception as exc:
            raise ScriptSecurityError(f"script load failed: {script_path}: {exc}") from exc

        for name, value in namespace.items():
            if name.startswith("on_") and callable(value):
                self._hooks[name] = value

    def run_hook(
        self,
        hook_name: str,
        *,
        context: HookContext,
        api: CapabilityAPI,
        budget_ms: int = 16,
    ) -> Any:
        hook = self._hooks.get(hook_name)
        if hook is None:
            return None

        started = time.perf_counter()
        try:
            result = hook(context, api)
        except ScriptSecurityError:
            raise
        except Exception as exc:
            raise ScriptSecurityError(f"hook {hook_name} failed: {exc}") from exc

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if elapsed_ms > budget_ms:
            raise ScriptSecurityError(
                f"hook {hook_name} exceeded budget: {elapsed_ms:.2f}ms > {budget_ms}ms"
            )
        return result
