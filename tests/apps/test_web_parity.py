"""Guards two web↔api contracts otherwise kept in sync by hand, by parsing the
TS source and comparing to the Python side so drift fails in CI:

  1. pipeline config defaults — web config.ts CONFIG_DEFAULTS vs PipelineRequest
  2. confidence tier cut-offs — web confidence.ts vs apps/api/confidence.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_TS = _ROOT / "apps" / "web" / "lib" / "config.ts"
_CONFIDENCE_TS = _ROOT / "apps" / "web" / "lib" / "confidence.ts"


def _parse_web_config_defaults() -> dict[str, object]:
    text = _CONFIG_TS.read_text()
    # CONFIG_DEFAULTS = { ... } — scalars only, so the first `}` closes it.
    m = re.search(r"CONFIG_DEFAULTS[^{]*\{(.*?)\}", text, re.S)
    assert m, f"could not locate CONFIG_DEFAULTS object in {_CONFIG_TS}"
    out: dict[str, object] = {}
    for key, raw in re.findall(r'(\w+):\s*("[^"]*"|[\d.]+)', m.group(1)):
        out[key] = raw.strip('"') if raw.startswith('"') else float(raw)
    assert out, "parsed no CONFIG_DEFAULTS entries — config.ts format changed?"
    return out


def test_pipeline_config_defaults_match_web() -> None:
    from apps.api.schemas import PipelineRequest

    api = PipelineRequest().model_dump()
    web = _parse_web_config_defaults()

    assert set(web) == set(api), (
        f"config-key drift — web-only={set(web) - set(api)}, "
        f"api-only={set(api) - set(web)}"
    )
    for key, api_val in api.items():
        web_val = web[key]
        if isinstance(api_val, bool):
            assert str(web_val).lower() == str(api_val).lower(), f"{key}: web={web_val} api={api_val}"
        elif isinstance(api_val, (int, float)):
            assert float(web_val) == float(api_val), f"{key}: web={web_val} api={api_val}"
        else:
            assert str(web_val) == str(api_val), f"{key}: web={web_val!r} api={api_val!r}"


def _parse_web_confidence() -> tuple[list[tuple[float, str, str]], tuple[str, str]]:
    text = _CONFIDENCE_TS.read_text()
    # `return {` anchors to the function body (skips the interface's word union).
    all_returns = re.findall(r'return\s*\{\s*key:\s*"(\w+)",\s*word:\s*"(\w+)"', text)
    thresholded = re.findall(
        r'score\s*>=\s*([\d.]+)\)\s*return\s*\{\s*key:\s*"(\w+)",\s*word:\s*"(\w+)"',
        text,
    )
    assert thresholded, f"parsed no thresholded tiers — confidence.ts format changed? ({_CONFIDENCE_TS})"
    rules = [(float(t), k, w) for t, k, w in thresholded]
    rule_pairs = {(k, w) for _, k, w in rules}
    fallbacks = [(k, w) for k, w in all_returns if (k, w) not in rule_pairs]
    assert len(fallbacks) == 1, f"expected exactly one fallback tier, got {fallbacks}"
    return rules, fallbacks[0]


def _web_tier(score: float, rules: list[tuple[float, str, str]], fallback: tuple[str, str]) -> tuple[str, str]:
    for threshold, key, word in rules:  # source order = descending threshold
        if score >= threshold:
            return key, word
    return fallback


@pytest.mark.parametrize(
    "score", [0.0, 0.1, 0.24, 0.249, 0.25, 0.26, 0.4, 0.499, 0.5, 0.501, 0.9, 1.0]
)
def test_confidence_tiers_match_web(score: float) -> None:
    from apps.api.confidence import confidence_tier

    rules, fallback = _parse_web_confidence()
    api = confidence_tier(score)
    assert (api.key, api.word) == _web_tier(score, rules, fallback), (
        f"confidence tier drift at score={score}: api={(api.key, api.word)} "
        f"web={_web_tier(score, rules, fallback)}"
    )
