from __future__ import annotations

from dataclasses import dataclass, field

from pvz.models import ModPackage
from pvz.scripting.runtime import CapabilityAPI, HookContext, HookRuntime


@dataclass
class ScriptModule:
    mod_id: str
    runtime: HookRuntime
    capabilities: set[str]


@dataclass
class ScriptManager:
    modules: list[ScriptModule] = field(default_factory=list)
    shared_state: dict = field(default_factory=dict)

    def load_from_mods(self, mods: list[ModPackage]) -> None:
        for mod in mods:
            for _, rel_path in mod.manifest.entrypoints.items():
                path = mod.path / rel_path
                runtime = HookRuntime()
                runtime.load_script(path)
                self.modules.append(
                    ScriptModule(
                        mod_id=mod.manifest.id,
                        runtime=runtime,
                        capabilities=set(mod.manifest.capabilities),
                    )
                )

    def run_hook(self, hook_name: str, *, context: HookContext) -> None:
        for module in self.modules:
            api = CapabilityAPI(capabilities=module.capabilities, state=self.shared_state)
            module.runtime.run_hook(hook_name, context=context, api=api)
