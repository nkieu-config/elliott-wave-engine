from __future__ import annotations

from engine.types import DegreeLabel, PatternKind, WaveRole

__all__ = [
    "USE_FRIENDLY",
    "family_label",
    "pattern_label",
    "role_label",
    "role_short",
    "degree_label_str",
]

# Flip to True for end-user-facing UI.
USE_FRIENDLY: bool = False


PATTERN_DISPLAY: dict[PatternKind, str] = {
    PatternKind.FIVE_TREND_S1_LONGEST: "5-Wave Trend · Wave 1 longest",
    PatternKind.FIVE_TREND_S3_LONGEST: "5-Wave Trend · Wave 3 longest",
    PatternKind.FIVE_TREND_S5_LONGEST: "5-Wave Trend · Wave 5 longest",
    PatternKind.FIVE_TREND_S5_SHORTER: "5-Wave Trend · Wave 5 shorter",
    PatternKind.FIVE_TREND_EQUAL_PUSH: "5-Wave Trend · Equal push",
    PatternKind.FIVE_SIDEWAY_CONTRACT: "5-Wave Sideway · Contract",
    PatternKind.FIVE_SIDEWAY_BALANCE: "5-Wave Sideway · Balance",
    PatternKind.FIVE_SIDEWAY_EXPAND: "5-Wave Sideway · Expand",
    PatternKind.THREE_NORMAL: "3-Wave · Normal",
    PatternKind.THREE_S2_LONGER: "3-Wave · Wave 2 longer",
    PatternKind.THREE_S3_SHORTER: "3-Wave · Wave 3 shorter",
    PatternKind.THREE_S2_LONGER_S3_SHORTER: "3-Wave · Wave 2 longer + Wave 3 shorter",
    PatternKind.LINK_T: "Link-Wave (+T) · Trend",
    PatternKind.LINK_S: "Link-Wave (+S) · Sideway",
    PatternKind.LINK_SE: "Link-Wave (+SE) · Sideway-Expand",
}


FAMILY_DISPLAY: dict[str, str] = {
    "5W_TREND": "5-Wave Trend",
    "5W_SIDEWAY": "5-Wave Sideway",
    "3W": "3-Wave",
    "LINK_T": "Link-Wave (+T)",
    "LINK_S": "Link-Wave (+S)",
    "LINK_SE": "Link-Wave (+SE)",
}


ROLE_DISPLAY: dict[str, str] = {
    "anchor": "Anchor",
    "s1": "Wave 1",
    "s2": "Wave 2",
    "s3": "Wave 3",
    "s4": "Wave 4",
    "s5": "Wave 5",
    "link": "Link",
    "set_1": "Set 1",
    "set_2": "Set 2",
    "set_3": "Set 3",
}


# Presenter-facing W1..W5 (vs parser-internal S1..S5).
ROLE_SHORT: dict[str, str] = {
    "anchor": "ANCHOR",
    "s1": "W1",
    "s2": "W2",
    "s3": "W3",
    "s4": "W4",
    "s5": "W5",
    "link": "LINK",
    "set_1": "SET1",
    "set_2": "SET2",
    "set_3": "SET3",
}


DEGREE_DISPLAY: dict[DegreeLabel, str] = {
    DegreeLabel.PRIMARY: "Primary",
    DegreeLabel.SECONDARY: "Secondary",
    DegreeLabel.MINOR: "Minor",
}


def _resolve_friendly(friendly: bool | None) -> bool:
    return USE_FRIENDLY if friendly is None else friendly


def _friendly_or_raw(friendly_label: str, raw: str, friendly: bool | None) -> str:
    return friendly_label if _resolve_friendly(friendly) else raw


def _role_key(role: WaveRole | str) -> str:
    return role.value if hasattr(role, "value") else str(role)


def pattern_label(kind: PatternKind | None, *, friendly: bool | None = None) -> str:
    if kind is None:
        return ""
    return _friendly_or_raw(PATTERN_DISPLAY.get(kind, kind.value), kind.value, friendly)


def family_label(family: str, *, friendly: bool | None = None) -> str:
    if not family:
        return ""
    return _friendly_or_raw(FAMILY_DISPLAY.get(family, family), family, friendly)


def role_label(role: WaveRole | str | None, *, friendly: bool | None = None) -> str:
    if role is None:
        return ""
    key = _role_key(role)
    return _friendly_or_raw(ROLE_DISPLAY.get(key, key), key, friendly)


def role_short(role: WaveRole | str | None) -> str:
    if role is None:
        return ""
    key = _role_key(role)
    return ROLE_SHORT.get(key, key.upper())


def degree_label_str(
    degree: DegreeLabel | None,
    *,
    friendly: bool | None = None,
) -> str:
    if degree is None:
        return ""
    return _friendly_or_raw(DEGREE_DISPLAY.get(degree, degree.value), degree.value, friendly)
