from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pvz.errors import ScriptSecurityError
from pvz.scripting import CapabilityAPI, HookContext, HookRuntime


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


class ScriptingTests(unittest.TestCase):
    def test_blocks_disallowed_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "mod.py"
            _write(
                script,
                """
import os

def on_startup(context, api):
    return os.getcwd()
""",
            )
            runtime = HookRuntime()
            with self.assertRaises(ScriptSecurityError):
                runtime.load_script(script)

    def test_capability_gate_blocks_state_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "mod.py"
            _write(
                script,
                """
def on_tick(context, api):
    api.set_state('counter', 1)
""",
            )
            runtime = HookRuntime()
            runtime.load_script(script)
            api = CapabilityAPI(capabilities=set(), state={})
            with self.assertRaises(ScriptSecurityError):
                runtime.run_hook("on_tick", context=HookContext(tick=1), api=api)

    def test_capability_allows_event_emission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "mod.py"
            _write(
                script,
                """
def on_tick(context, api):
    api.emit_event('tick', {'n': context.tick})
""",
            )
            runtime = HookRuntime()
            runtime.load_script(script)
            state = {}
            api = CapabilityAPI(capabilities={"events.emit"}, state=state)
            runtime.run_hook("on_tick", context=HookContext(tick=3), api=api)
            self.assertEqual(state["events"][0]["event"], "tick")


if __name__ == "__main__":
    unittest.main()
