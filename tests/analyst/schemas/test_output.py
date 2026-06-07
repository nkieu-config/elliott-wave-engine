from analyst.schemas.analysis import AnalysisResult
from analyst.schemas.citation import CitationReport
from analyst.schemas.output import AnalysisOutput


def test_analysis_result_defaults():
    r = AnalysisResult(scenario_id="abc")
    assert r.scenario_id == "abc"
    assert r.bottleneck is None
    assert r.confirmation is None
    assert r.targets is None
    assert r.scenario_diffs == ()


def test_analysis_output_layer1_only_when_no_llm():
    layer1 = AnalysisResult(scenario_id="abc")
    out = AnalysisOutput(
        scenario_id="abc",
        mode="explanation",
        layer1=layer1,
        narration=None,
        citations=(),
        citation_report=CitationReport(),
        model_id=None,
        prompt_version="v0",
        cached=False,
    )
    assert out.narration is None
    assert out.layer1 is layer1
    assert out.fell_back is False
