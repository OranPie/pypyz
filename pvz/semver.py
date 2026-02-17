from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, raw: str) -> "SemVer":
        parts = raw.strip().split(".")
        if len(parts) != 3:
            raise ValueError(f"invalid semver: {raw}")
        return cls(*(int(p) for p in parts))


def satisfies(version: str, constraint: str) -> bool:
    if not constraint:
        return True
    v = SemVer.parse(version)
    c = constraint.strip()

    if "," in c:
        return all(satisfies(version, piece.strip()) for piece in c.split(","))

    if c.startswith("^"):
        base = SemVer.parse(c[1:])
        return v >= base and v.major == base.major
    if c.startswith("~"):
        base = SemVer.parse(c[1:])
        return v >= base and (v.major, v.minor) == (base.major, base.minor)

    ops = [">=", "<=", ">", "<", "=="]
    for op in ops:
        if c.startswith(op):
            rhs = SemVer.parse(c[len(op) :])
            if op == ">=":
                return v >= rhs
            if op == "<=":
                return v <= rhs
            if op == ">":
                return v > rhs
            if op == "<":
                return v < rhs
            return v == rhs

    return v == SemVer.parse(c)
