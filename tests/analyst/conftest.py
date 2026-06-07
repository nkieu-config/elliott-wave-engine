import pytest

from analyst.schemas.analysis import AnalysisResult
from analyst.schemas.bottleneck import BottleneckDiagnosis
from analyst.schemas.citation import TheoryRef
from analyst.schemas.confirmation import ConfirmationLevel, ConfirmationReport
from engine.parser.output.types import Scenario
from tests.analyst._helpers import make_scenario


@pytest.fixture
def simple_5wt_scenario() -> Scenario:
    return make_scenario()


@pytest.fixture
def layer1_result(simple_5wt_scenario):
    bd = BottleneckDiagnosis(
        slot_name="pull_depth_discipline", slot_value=0.6, dimension="structural",
        is_dim_minimum=True, is_overall_minimum=True, gap_to_next=0.1,
        intermediates={}, plain_explanation="Slot scored 0.6.",
        theory_ref=TheoryRef(pages=(99, 100), concept="Fib Retracement window",
                             binding="concept_operationalization", note="..."),
    )
    cr = ConfirmationReport(
        family="5W_TREND",
        levels=(
            ConfirmationLevel("L1", "s2-s4 trendline broken", True, 200, 33),
        ),
    )
    return AnalysisResult(scenario_id="t1", bottleneck=bd, confirmation=cr, targets=None)
