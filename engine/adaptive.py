from __future__ import annotations

from typing import Literal, get_args

from engine.types import PatternKind, TrendDir, WaveRole

__all__ = [
    "Family",
    "KIND_TO_FAMILY",
    "ALL_LINK",
    "allowed_sub_families",
    "allowed_sub_patterns",
    "expected_direction",
    "is_push_role",
]

Family = Literal["5W_TREND", "5W_SIDEWAY", "3W", "LINK_T", "LINK_S", "LINK_SE"]

# Derived from the Literal so the two can never drift — Family is the single source.
KNOWN_FAMILIES: frozenset[str] = frozenset(get_args(Family))

_FIVE_WAVE_LEG_ROLES: frozenset[WaveRole] = frozenset(
    {
        WaveRole.S1,
        WaveRole.S2,
        WaveRole.S3,
        WaveRole.S4,
        WaveRole.S5,
    }
)
_THREE_WAVE_LEG_ROLES: frozenset[WaveRole] = frozenset(
    {
        WaveRole.S1,
        WaveRole.S2,
        WaveRole.S3,
    }
)
_PUSH_ROLES: frozenset[WaveRole] = frozenset({WaveRole.S1, WaveRole.S3, WaveRole.S5})
_PULL_ROLES: frozenset[WaveRole] = frozenset({WaveRole.S2, WaveRole.S4})
_LINK_SET_SLOTS: frozenset[WaveRole] = frozenset(
    {
        WaveRole.SET_1,
        WaveRole.SET_2,
        WaveRole.SET_3,
    }
)


ALL_FIVE_TREND: frozenset[PatternKind] = frozenset(
    {
        PatternKind.FIVE_TREND_S1_LONGEST,
        PatternKind.FIVE_TREND_S3_LONGEST,
        PatternKind.FIVE_TREND_S5_LONGEST,
        PatternKind.FIVE_TREND_S5_SHORTER,
        PatternKind.FIVE_TREND_EQUAL_PUSH,
    }
)

FIVE_TREND_NO_S5_SHORTER: frozenset[PatternKind] = frozenset(
    ALL_FIVE_TREND - {PatternKind.FIVE_TREND_S5_SHORTER}
)

ALL_FIVE_SIDEWAY: frozenset[PatternKind] = frozenset(
    {
        PatternKind.FIVE_SIDEWAY_CONTRACT,
        PatternKind.FIVE_SIDEWAY_BALANCE,
        PatternKind.FIVE_SIDEWAY_EXPAND,
    }
)

ALL_THREE: frozenset[PatternKind] = frozenset(
    {
        PatternKind.THREE_NORMAL,
        PatternKind.THREE_S2_LONGER,
        PatternKind.THREE_S3_SHORTER,
        PatternKind.THREE_S2_LONGER_S3_SHORTER,
    }
)

ALL_LINK: frozenset[PatternKind] = frozenset(
    {
        PatternKind.LINK_T,
        PatternKind.LINK_S,
        PatternKind.LINK_SE,
    }
)

ALL_PATTERNS: frozenset[PatternKind] = ALL_FIVE_TREND | ALL_FIVE_SIDEWAY | ALL_THREE | ALL_LINK


KIND_TO_FAMILY: dict[PatternKind, Family] = {
    **{k: "5W_TREND" for k in ALL_FIVE_TREND},
    **{k: "5W_SIDEWAY" for k in ALL_FIVE_SIDEWAY},
    **{k: "3W" for k in ALL_THREE},
    PatternKind.LINK_T: "LINK_T",
    PatternKind.LINK_S: "LINK_S",
    PatternKind.LINK_SE: "LINK_SE",
}


def _valid_leg_roles(family: Family) -> frozenset[WaveRole]:
    if family in ("5W_TREND", "5W_SIDEWAY"):
        return _FIVE_WAVE_LEG_ROLES
    if family == "3W":
        return _THREE_WAVE_LEG_ROLES
    if family in ("LINK_T", "LINK_S", "LINK_SE"):
        return _LINK_SET_SLOTS | {WaveRole.LINK}
    return frozenset()


# EW sub-pattern grammar as data: per family, an ordered list of (matching roles,
# allowed sub-patterns). The first entry whose role-set contains the role wins;
# a `None` role-set is the catch-all default (Pull legs) and must come last.
_S1_S3: frozenset[WaveRole] = frozenset({WaveRole.S1, WaveRole.S3})
_S5: frozenset[WaveRole] = frozenset({WaveRole.S5})

_TREND_PUSH_SUBS = frozenset(FIVE_TREND_NO_S5_SHORTER | {PatternKind.THREE_NORMAL, PatternKind.LINK_T})
_TREND_S5_SUBS = frozenset(ALL_FIVE_TREND | {PatternKind.THREE_NORMAL, PatternKind.LINK_T})
_SIDEWAY_S5_SUBS = frozenset(ALL_FIVE_TREND | ALL_FIVE_SIDEWAY | ALL_THREE | {PatternKind.LINK_T})
_PUSH_TREND_OR_THREE_SUBS = frozenset(ALL_FIVE_TREND | ALL_THREE | {PatternKind.LINK_T})

# +S/+SE Pull connector p.86: 5W_TREND / 3W_NORMAL / +T only (== _TREND_S5_SUBS).
_LINK_S_RULES: tuple[tuple[frozenset[WaveRole] | None, frozenset[PatternKind]], ...] = (
    (_LINK_SET_SLOTS, frozenset(ALL_THREE | ALL_FIVE_SIDEWAY)),
    (None, _TREND_S5_SUBS),
)

_SUB_PATTERN_RULES: dict[
    Family, tuple[tuple[frozenset[WaveRole] | None, frozenset[PatternKind]], ...]
] = {
    "LINK_T": (
        (_LINK_SET_SLOTS, ALL_THREE),
        (None, ALL_PATTERNS),
    ),
    "LINK_S": _LINK_S_RULES,
    "LINK_SE": _LINK_S_RULES,
    "5W_TREND": (
        (_S1_S3, _TREND_PUSH_SUBS),
        (_S5, _TREND_S5_SUBS),
        (None, ALL_PATTERNS),  # S2/S4 Pull p.81
    ),
    "5W_SIDEWAY": (
        (_S5, _SIDEWAY_S5_SUBS),
        (None, _PUSH_TREND_OR_THREE_SUBS),
    ),
    "3W": (
        (_S1_S3, _PUSH_TREND_OR_THREE_SUBS),
        (None, ALL_PATTERNS),  # S2 Pull p.84
    ),
}


def allowed_sub_patterns(family: Family, role: WaveRole) -> frozenset[PatternKind]:
    if family not in KNOWN_FAMILIES:
        raise ValueError(f"unknown family {family!r}; expected one of {sorted(KNOWN_FAMILIES)}")

    valid_roles = _valid_leg_roles(family)
    if role not in valid_roles:
        raise ValueError(
            f"role {role.value!r} is not a leg of family {family!r}; "
            f"expected one of {sorted(r.value for r in valid_roles)}"
        )

    for roles, patterns in _SUB_PATTERN_RULES[family]:
        if roles is None or role in roles:
            return patterns
    return frozenset()  # unreachable: a validated role is always covered by a rule


def allowed_sub_families(family: Family, role: WaveRole) -> tuple[str, ...]:
    kinds = allowed_sub_patterns(family, role)
    return tuple(sorted({KIND_TO_FAMILY[k] for k in kinds if k in KIND_TO_FAMILY}))


_WITH_TREND_ROLES: frozenset[WaveRole] = _PUSH_ROLES | _LINK_SET_SLOTS
_AGAINST_TREND_ROLES: frozenset[WaveRole] = _PULL_ROLES | {WaveRole.LINK}


def is_push_role(family: Family, role: WaveRole) -> bool:
    del family
    if role in _WITH_TREND_ROLES:
        return True
    if role in _AGAINST_TREND_ROLES:
        return False
    raise ValueError(
        f"role {role.value!r} has no Push/Pull classification; "
        f"expected one of s1..s5 / SET_* / LINK"
    )


def expected_direction(family: Family, role: WaveRole, trend: TrendDir) -> TrendDir:
    if is_push_role(family, role):
        return trend
    return "down" if trend == "up" else "up"
