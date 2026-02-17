from __future__ import annotations

import heapq
from collections import defaultdict

from pvz.errors import DependencyError
from pvz.models import ModPackage
from pvz.semver import satisfies


def _check_constraints(mods: dict[str, ModPackage]) -> None:
    for mod in mods.values():
        manifest = mod.manifest
        for dep in manifest.requires:
            target = mods.get(dep.id)
            if target is None:
                raise DependencyError(f"{manifest.id} requires missing mod {dep.id}")
            if dep.version and not satisfies(target.manifest.version, dep.version):
                raise DependencyError(
                    f"{manifest.id} requires {dep.id} {dep.version}, got {target.manifest.version}"
                )

        for conflict in manifest.conflicts:
            target = mods.get(conflict.id)
            if target is None:
                continue
            if not conflict.version or satisfies(target.manifest.version, conflict.version):
                version_hint = f" {conflict.version}" if conflict.version else ""
                raise DependencyError(
                    f"{manifest.id} conflicts with {conflict.id}{version_hint}"
                )


def resolve_load_order(mods: dict[str, ModPackage]) -> list[ModPackage]:
    _check_constraints(mods)

    graph: dict[str, set[str]] = defaultdict(set)
    indegree: dict[str, int] = {mod_id: 0 for mod_id in mods.keys()}

    def add_edge(before: str, after: str) -> None:
        if before not in mods or after not in mods:
            return
        if after in graph[before]:
            return
        graph[before].add(after)
        indegree[after] += 1

    for mod_id, mod in mods.items():
        manifest = mod.manifest
        for dep in manifest.requires:
            add_edge(dep.id, mod_id)
        for other in manifest.load_after:
            add_edge(other, mod_id)
        for other in manifest.load_before:
            add_edge(mod_id, other)

    heap = [mod_id for mod_id, count in indegree.items() if count == 0]
    heapq.heapify(heap)
    result: list[str] = []

    while heap:
        current = heapq.heappop(heap)
        result.append(current)
        for nxt in sorted(graph[current]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                heapq.heappush(heap, nxt)

    if len(result) != len(mods):
        stuck = [mod_id for mod_id, count in indegree.items() if count > 0]
        raise DependencyError(f"dependency cycle detected: {sorted(stuck)}")

    return [mods[mod_id] for mod_id in result]
