from __future__ import annotations

from engine import display
from engine.display import (
    FAMILY_DISPLAY,
    PATTERN_DISPLAY,
    ROLE_DISPLAY,
    family_label,
    pattern_label,
    role_label,
)
from engine.types import PatternKind, WaveRole


def test_dev_mode_returns_raw_values_by_default() -> None:
    assert display.USE_FRIENDLY is False
    assert pattern_label(PatternKind.FIVE_TREND_S3_LONGEST) == "5W_TREND_S3_LONGEST"
    assert family_label("5W_TREND") == "5W_TREND"
    assert role_label(WaveRole.S3) == "s3"


def test_friendly_flag_switches_to_human_readable() -> None:
    assert pattern_label(PatternKind.FIVE_TREND_S3_LONGEST, friendly=True) == (
        "5-Wave Trend · Wave 3 longest"
    )
    assert family_label("5W_TREND", friendly=True) == "5-Wave Trend"
    assert role_label(WaveRole.S3, friendly=True) == "Wave 3"


def test_friendly_falls_back_to_raw_when_unmapped() -> None:
    assert family_label("UNKNOWN_FAMILY", friendly=True) == "UNKNOWN_FAMILY"
    assert role_label("custom_role", friendly=True) == "custom_role"


def test_none_inputs_return_empty_string() -> None:
    assert pattern_label(None) == ""
    assert family_label("") == ""
    assert role_label(None) == ""


def test_role_label_accepts_raw_string_or_enum() -> None:
    assert role_label("s1") == "s1"
    assert role_label(WaveRole.S1) == "s1"
    assert role_label("s1", friendly=True) == "Wave 1"
    assert role_label(WaveRole.S1, friendly=True) == "Wave 1"


def test_every_pattern_kind_has_display_entry() -> None:
    for kind in PatternKind:
        assert kind in PATTERN_DISPLAY, f"missing display for {kind}"


def test_every_role_has_display_entry() -> None:
    for role in WaveRole:
        assert role.value in ROLE_DISPLAY, f"missing display for role {role}"


def test_module_switch_applies_when_flag_omitted() -> None:
    original = display.USE_FRIENDLY
    try:
        display.USE_FRIENDLY = True
        assert pattern_label(PatternKind.THREE_NORMAL) == "3-Wave · Normal"
        assert family_label("3W") == "3-Wave"
        assert role_label(WaveRole.S2) == "Wave 2"
    finally:
        display.USE_FRIENDLY = original


def test_known_family_strings_have_entries() -> None:
    for family in ("5W_TREND", "5W_SIDEWAY", "3W", "LINK_T", "LINK_S", "LINK_SE"):
        assert family in FAMILY_DISPLAY, f"missing family: {family}"
