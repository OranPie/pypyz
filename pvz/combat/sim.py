from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BattleState:
    sun: int
    lawns: int
    active_plants: list[dict[str, Any]] = field(default_factory=list)
    active_zombies: list[dict[str, Any]] = field(default_factory=list)
    tick: int = 0


def simulate_wave(state: BattleState, *, duration_ticks: int = 10) -> dict[str, Any]:
    """Small deterministic simulation stub for validating content wiring."""
    for _ in range(duration_ticks):
        state.tick += 1

        for plant in state.active_plants:
            plant_damage = int(plant.get("damage", 0))
            if state.active_zombies and plant_damage > 0:
                state.active_zombies[0]["hp"] = max(0, state.active_zombies[0].get("hp", 0) - plant_damage)

        state.active_zombies = [z for z in state.active_zombies if z.get("hp", 0) > 0]

        for zombie in state.active_zombies:
            state.sun = max(0, state.sun - int(zombie.get("drain_sun", 0)))

    return {
        "tick": state.tick,
        "sun": state.sun,
        "zombies_left": len(state.active_zombies),
    }
