from analyst.prompts import (
    build_prompt,
    differentiator,
    explanation,
    scenario_outlook,
)


def test_build_prompt_for_each_mode_includes_layer1_and_theory():
    for mode in ("explanation", "slot_focus", "differentiator", "scenario_outlook"):
        system, user = build_prompt(
            mode=mode,
            layer1_md="LAYER1-CONTENT",
            theory_md="THEORY-CONTENT",
        )
        assert "LAYER1-CONTENT" in user
        assert "THEORY-CONTENT" in user
        assert "Elliott Wave analyst" in system
        assert "Elliott Wave analyst" not in user


def test_modes_have_different_user_questions():
    users = [
        build_prompt(m, "L", "T")[1]
        for m in ("explanation", "slot_focus", "differentiator", "scenario_outlook")
    ]
    assert len(set(users)) == 4


def test_differentiator_prompt_handles_absent_diff_block():
    assert "only one scenario" in differentiator.USER_PROMPT


def test_outlook_prompt_covers_projection_succession_and_no_advice():
    p = scenario_outlook.USER_PROMPT
    assert "projected" in p
    assert "follow this pattern" in p.lower()
    assert "buy/sell" in p
    assert "disclosure" in p


def test_slot_focus_prompt_owns_the_invalidation_line():
    from analyst.prompts import slot_focus
    p = slot_focus.USER_PROMPT.lower()
    assert "invalidation" in p
    assert "risk" in p


def test_explanation_prompt_asks_for_interpretation_not_recitation():
    p = explanation.USER_PROMPT
    assert "verbatim" not in p
    assert "reliability" in p
