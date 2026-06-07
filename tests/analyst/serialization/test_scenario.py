from analyst.serialization.scenario import serialize_scenario
from tests.analyst._helpers import make_scenario


def test_serialize_includes_identity_tree_slots(simple_5wt_scenario, layer1_result):
    md = serialize_scenario(simple_5wt_scenario, layer1_result)
    assert "**Family:** 5-Wave Trend" in md
    assert "ROOT" in md
    assert "Shape-and-proportion checks" in md
    assert "structural_total" not in md
    assert "Bottleneck Diagnosis" in md


def test_explanation_mode_omits_confirmation_and_targets(
    simple_5wt_scenario, layer1_result,
):
    md = serialize_scenario(simple_5wt_scenario, layer1_result, "explanation")
    assert "Bottleneck Diagnosis" in md
    assert "Score Components" in md
    assert "## Verifier" in md
    assert "## Confirmation" not in md
    assert "## Targets" not in md


def test_scenario_outlook_mode_omits_slots_and_bottleneck(
    simple_5wt_scenario, layer1_result,
):
    md = serialize_scenario(simple_5wt_scenario, layer1_result, "scenario_outlook")
    assert "## Confirmation" in md
    assert "Score Components" not in md
    assert "Bottleneck Diagnosis" not in md


def test_differentiator_mode_includes_scenario_comparison_block(
    simple_5wt_scenario, layer1_result,
):
    md = serialize_scenario(simple_5wt_scenario, layer1_result, "differentiator")
    assert "## Scenario Comparison" in md
    expl = serialize_scenario(simple_5wt_scenario, layer1_result, "explanation")
    assert "## Scenario Comparison" not in expl


def test_verifier_block_reports_passed_for_a_complete_scenario(
    simple_5wt_scenario, layer1_result,
):
    md = serialize_scenario(simple_5wt_scenario, layer1_result, "explanation")
    assert "## Verifier" in md
    assert "PASSED" in md
    assert "5-Wave Trend · Wave 3 longest" in md
    assert "5W_TREND_S3_LONGEST" not in md


def test_verifier_block_reports_not_run_for_an_incomplete_scenario(layer1_result):
    sc = make_scenario(
        family="3W",
        pattern_kind=None,
        pivots=[
            (100.0, 0, "low"),
            (140.0, 40, "high"),
            (120.0, 50, "low"),
        ],
        score=0.2,
        scenario_id="open1",
        score_components={},
    )
    md = serialize_scenario(sc, layer1_result, "explanation")
    assert "NOT RUN" in md
    assert "2 leg(s) parsed" in md
    assert "not passed cleanly" in md
