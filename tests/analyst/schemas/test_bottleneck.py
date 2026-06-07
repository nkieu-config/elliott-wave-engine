from analyst.schemas.bottleneck import BottleneckDiagnosis
from analyst.schemas.citation import TheoryRef


def test_bottleneck_diagnosis_required_fields():
    bd = BottleneckDiagnosis(
        slot_name="leg_smoothness",
        slot_value=0.589,
        dimension="visual",
        is_dim_minimum=True,
        is_overall_minimum=True,
        gap_to_next=0.123,
        intermediates={"per_leg": []},
        plain_explanation="leg_smoothness scored 0.589 — the weakest slot.",
        theory_ref=TheoryRef(pages=(), concept="Chart appearance",
                             binding="heuristic", note="no theory binding"),
    )
    assert bd.slot_name == "leg_smoothness"
    assert bd.dimension == "visual"
