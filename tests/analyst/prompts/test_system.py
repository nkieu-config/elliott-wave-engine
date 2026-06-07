from analyst.prompts.system import PROMPT_VERSION, SYSTEM_PROMPT


def test_system_prompt_contains_essential_rules():
    p = SYSTEM_PROMPT
    assert "ground truth" in p
    assert "binding" in p
    assert PROMPT_VERSION


def test_system_prompt_specifies_structured_json_output():
    p = SYSTEM_PROMPT
    assert "JSON" in p
    assert '"paragraphs"' in p
    assert "data_observation" in p
    assert "theory_claim" in p
    assert "disclosure" in p


def test_system_prompt_softens_empty_blocks_and_arithmetic():
    p = SYSTEM_PROMPT
    assert "empty or absent" in p
    assert "do not refuse" in p
    assert "Interpret" in p
    assert "arithmetic chain" in p


def test_system_prompt_requires_plain_slot_language():
    p = SYSTEM_PROMPT
    assert "raw identifier" in p
    assert "leg_smoothness" in p


def test_system_prompt_carries_the_scoring_slot_glossary():
    p = SYSTEM_PROMPT
    for raw, plain in [
        ("speed_cluster", "the wave-pacing check"),
        ("fib_push_pairs", "the Fibonacci-proportion check"),
        ("pull_depth_discipline", "the pullback-depth check"),
        ("pivot_sharpness", "the pivot-sharpness check"),
        ("leg_smoothness", "the swing-smoothness check"),
    ]:
        assert raw in p
        assert plain in p


def test_system_prompt_bans_internal_data_block_names():
    p = SYSTEM_PROMPT
    assert '"the targets block"' in p


def test_system_prompt_bans_leg_codes_and_link_codes():
    p = SYSTEM_PROMPT
    assert "S2" in p
    assert "S4" in p
    assert '"Wave 2"' in p
    assert "+T" in p
    assert "+S" in p
    assert '"Trend linkage"' in p
    assert '"Sideway linkage"' in p


def test_system_prompt_bans_internal_system_components():
    p = SYSTEM_PROMPT
    assert '"the verifier"' in p
    assert '"Layer-1"' in p
    assert '"the gate"' in p


def test_system_prompt_bans_procedural_recitation():
    p = SYSTEM_PROMPT
    assert "procedural recitation" in p.lower() or "Interpret, do not recite" in p


def test_prompt_version_is_the_current_editorial_label():
    assert PROMPT_VERSION == "v2.14"
