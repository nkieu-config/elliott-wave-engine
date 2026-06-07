from analyst.schemas.confirmation import (
    ConfirmationLevel,
    ConfirmationReport,
)


def test_levels_report_with_partial_progress():
    rep = ConfirmationReport(
        family="5W_TREND",
        levels=(
            ConfirmationLevel(name="L1", condition="s2-s4 trendline broken",
                              met=True, triggered_at_bar=200, theory_page=33),
            ConfirmationLevel(name="L2", condition="s5 retraced 100%",
                              met=False, triggered_at_bar=None, theory_page=34),
        ),
    )
    assert rep.highest_met == "L1"
    assert rep.is_applicable
    assert rep.not_applicable_reason is None


def test_not_applicable_report():
    rep = ConfirmationReport.not_applicable(
        family="5W_SIDEWAY",
        reason="Expand has no s2-s4 trendline (p.43)",
        citation=43,
    )
    assert rep.levels == ()
    assert not rep.is_applicable
    assert rep.highest_met is None
    assert rep.not_applicable_reason.citation == 43
