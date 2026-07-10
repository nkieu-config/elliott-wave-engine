"""Wire-contract tests for the pipeline → JSON serializers: lock the shape the
Next.js client depends on (JSON-safe, expected keys, mirrors the engine's top
scenario + counts) since a drift silently breaks the frontend.
"""

from __future__ import annotations

import json

import pytest

from apps.api.serializers import serialize_scenario
from tests.analyst._helpers import make_scenario

PIPELINE_KEYS = {
    "meta",
    "bars",
    "raw_pivots",
    "active_pivots",
    "selected_anchor",
    "report",
    "top_scenario",
    "top_scenario_layer1",
    "scenario_counts",
    "load_error",
}

LAYER1_KEYS = {
    "scenario_id",
    "bottleneck",
    "confirmation",
    "targets",
    "succession",
    "decision",
    "alternative",
    "score_intermediates",
}


@pytest.mark.slow
def test_pipeline_payload_is_json_serializable(payload):
    # Raises TypeError if a datetime / enum / dataclass leaks onto the wire.
    json.dumps(payload)


@pytest.mark.slow
def test_pipeline_payload_has_expected_keys(payload):
    # Exact (not superset) so an extra/renamed wire key is caught.
    assert set(payload) == PIPELINE_KEYS


@pytest.mark.slow
def test_report_carries_diagnostic(payload):
    # Phase-A fix: diagnostic (death_reason + actionable hint) must be on the wire.
    diag = payload["report"]["diagnostic"]
    assert {
        "death_reason",
        "suggested_action",
        "first_divergence_index",
        "last_alive_segment_index",
    } <= set(diag)


@pytest.mark.parametrize(
    "total, word",
    [(0.80, "Strong"), (0.50, "Strong"), (0.49, "Moderate"),
     (0.25, "Moderate"), (0.24, "Low"), (0.0, "Low")],
)
def test_confidence_tier_wired_from_headline_total(total, word):
    # Behavioral: the serialized tier follows score_components["total"] through the
    # real cut-offs — a tautological "key in {low,mid,high}" would miss a mis-tier.
    ser = serialize_scenario(make_scenario(score_components={"total": total}))
    assert ser.confidence_tier.word == word


def test_confidence_tier_uses_total_not_raw_score():
    # Headline is score_components["total"], not scenario.score; a swap would mis-tier.
    ser = serialize_scenario(make_scenario(score=0.10, score_components={"total": 0.62}))
    assert ser.confidence_tier.word == "Strong"  # 0.62 total, not 0.10 score


@pytest.mark.slow
def test_top_scenario_matches_engine(payload, top_scenario):
    ser = payload["top_scenario"]
    assert ser is not None
    assert ser["id"] == top_scenario.id
    assert ser["score"] == top_scenario.score
    assert ser["score_components"] == dict(top_scenario.score_components)
    # Tier must match the headline against the real cut-offs (not just "some valid key").
    headline = top_scenario.score_components.get("total", top_scenario.score)
    expected_key = "high" if headline >= 0.50 else "mid" if headline >= 0.25 else "low"
    assert ser["confidence_tier"]["key"] == expected_key


@pytest.mark.slow
def test_all_scenarios_serialized(payload, pipeline_result):
    assert len(payload["report"]["scenarios"]) == len(pipeline_result.report.scenarios)


@pytest.mark.slow
def test_scenario_counts_consistent(payload):
    counts = payload["scenario_counts"]
    assert counts["complete"] + counts["open"] == counts["total"]


@pytest.mark.slow
def test_layer1_payload_is_json_safe_and_complete(layer1_payload, top_scenario):
    json.dumps(layer1_payload)
    assert set(layer1_payload) == LAYER1_KEYS
    assert layer1_payload["scenario_id"] == top_scenario.id
    # Decision carries the stage subtext fields the UI surfaces.
    decision = layer1_payload["decision"]
    assert decision is not None
    assert "wave_progress_pct" in decision
    assert "open_wave_start" in decision
