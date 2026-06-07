from analyst.diagnostics.education import FAMILY_EDUCATION, family_education


def test_every_active_family_has_an_education_entry():
    expected = {"5W_TREND", "5W_SIDEWAY", "3W", "LINK_T", "LINK_S", "LINK_SE"}
    assert expected.issubset(set(FAMILY_EDUCATION))


def test_each_entry_carries_rules_and_visual_cues():
    for family, edu in FAMILY_EDUCATION.items():
        assert edu.title, family
        assert edu.one_line, family
        assert len(edu.rules) >= 2, family
        assert len(edu.visual_cues) >= 2, family


def test_family_education_returns_none_for_unknown_family():
    assert family_education("UNKNOWN_PATTERN") is None
    assert family_education("") is None


def test_education_text_avoids_leaked_codes():
    banned_substrings = ("+T", "+S", "+SE",
                         "5W_TREND", "5W_SIDEWAY", "LINK_T", "LINK_S")
    for family, edu in FAMILY_EDUCATION.items():
        all_text = (
            edu.one_line + " "
            + " ".join(edu.rules) + " "
            + " ".join(edu.visual_cues)
        )
        for code in banned_substrings:
            assert code not in all_text, f"{family} leaks {code}: {all_text}"
