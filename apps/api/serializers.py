"""Pipeline → response-model serializers shared by the API and the offline export.
The wire shape lives once, in ``schemas_responses``; these functions only map
domain objects onto it, so serializer↔model drift is impossible by construction."""

from __future__ import annotations

from typing import Any

from analyst.enums import enum_value, enum_value_or_none
from analyst.schemas.analysis import AnalysisResult
from analyst.schemas.bottleneck import BottleneckDiagnosis
from analyst.schemas.citation import TheoryRef
from analyst.schemas.confirmation import ConfirmationLevel, ConfirmationReport
from analyst.schemas.decision import AlternativeBrief, DecisionSummary, PriceMove
from analyst.schemas.succession import NextPattern, SuccessionReport
from analyst.schemas.targets import Target, TargetSet
from analyst.taxonomy import humanize_family_codes
from apps.api import pipeline_ops
from apps.api.confidence import confidence_tier
from apps.api.schemas_responses import (
    AlternativeBriefOut,
    BarOut,
    BottleneckOut,
    ConfidenceTierOut,
    ConfirmationLevelOut,
    ConfirmationReportOut,
    DecisionSummaryOut,
    DiagnosticOut,
    Layer1Response,
    LinkSetOut,
    MetaOut,
    NextPatternOut,
    NotApplicableReasonOut,
    PipelineResponse,
    PivotOut,
    PriceMoveOut,
    ReportOut,
    ScenarioCountsOut,
    ScenarioOut,
    SegmentOut,
    SuccessionReportOut,
    TargetOut,
    TargetSetOut,
    TheoryRefOut,
    WaveOut,
)
from engine import (
    AnalysisReport,
    Bar,
    PipelineResult,
    Pivot,
    Scenario,
    Segment,
    WaveNode,
)
from engine.display import family_label, pattern_label


def serialize_bar(b: Bar) -> BarOut:
    return BarOut(
        time=b.time.isoformat(),
        open=b.open,
        high=b.high,
        low=b.low,
        close=b.close,
        volume=b.volume,
    )


def serialize_pivot(p: Pivot) -> PivotOut:
    return PivotOut(
        index=p.index,
        time=p.time.isoformat(),
        price=p.price,
        kind=p.kind,
        bar_index=p.bar_index,
    )


def serialize_segment(s: Segment) -> SegmentOut:
    return SegmentOut(start=serialize_pivot(s.start), end=serialize_pivot(s.end))


def _serialize_link_set(s: Any) -> LinkSetOut:
    # Raw pattern_kind stays for cache keys; label saves the client re-implementing it.
    raw = enum_value(s.pattern_kind)
    return LinkSetOut(
        pattern_kind=raw,
        pattern_label=pattern_label(s.pattern_kind, friendly=True) or raw,
        leg_start=s.leg_start,
        leg_end=s.leg_end,
        degree_label=enum_value_or_none(s.degree_label),
    )


def serialize_wave(node: WaveNode) -> WaveOut:
    return WaveOut(
        role=enum_value(node.role),
        pattern_kind=enum_value_or_none(node.pattern_kind),
        degree_label=enum_value_or_none(node.degree_label),
        span_start=serialize_pivot(node.span_start),
        span_end=serialize_pivot(node.span_end) if node.span_end else None,
        nesting_level=node.nesting_level,
        segments=[serialize_segment(s) for s in node.segments],
        children=[serialize_wave(c) for c in node.children],
        # Link-wave nodes only: how the link's children group into sub-patterns.
        sets=([_serialize_link_set(s) for s in node.sets] if node.sets else None),
    )


def serialize_scenario(s: Scenario) -> ScenarioOut:
    pattern_raw = enum_value_or_none(s.pattern_kind)
    components = dict(s.score_components or {})
    # score_components["total"] is the canonical headline; fall back to score.
    headline = float(components.get("total", s.score))
    tier = confidence_tier(headline)
    return ScenarioOut(
        id=s.id,
        score=s.score,
        score_components=components,
        family=s.family,
        family_label=family_label(s.family, friendly=True) or s.family,
        pattern_kind=pattern_raw,
        pattern_label=(
            pattern_label(s.pattern_kind, friendly=True) if s.pattern_kind else None
        ),
        is_complete=s.is_complete,
        depth=s.depth,
        confidence_tier=ConfidenceTierOut(key=tier.key, word=tier.word),
        root=serialize_wave(s.root),
        # Open sub-pattern tree the chart's in-progress projection walks.
        open_subtree=serialize_wave(s.open_subtree) if s.open_subtree else None,
    )


def serialize_diagnostic(d: Any) -> DiagnosticOut:
    # Why a parse died + suggested action, for the hero's no-scenarios banner.
    return DiagnosticOut(
        death_reason=d.death_reason,
        suggested_action=d.suggested_action,
        first_divergence_index=d.first_divergence_index,
        last_alive_segment_index=d.last_alive_segment_index,
    )


def serialize_report(r: AnalysisReport | None) -> ReportOut | None:
    if r is None:
        return None
    return ReportOut(
        anchor=serialize_pivot(r.anchor) if r.anchor else None,
        segments=[serialize_segment(s) for s in r.segments],
        scenarios=[serialize_scenario(s) for s in r.scenarios],
        diagnostic=serialize_diagnostic(r.diagnostic),
        summary=r.summary,
    )


def serialize_pipeline(
    result: PipelineResult,
    *,
    meta: dict[str, Any],
    top_scenario_layer1: Layer1Response | None = None,
) -> PipelineResponse:
    # top_scenario_layer1, when present, seeds the client's cache to skip a second roundtrip.
    scenarios = result.report.scenarios if result.report else ()
    top = pipeline_ops.top_scenario(scenarios)
    # "complete" requires both is_complete AND a classified pattern_kind.
    n_complete = sum(1 for s in scenarios if s.is_complete and s.pattern_kind)
    n_open = len(scenarios) - n_complete

    return PipelineResponse(
        meta=MetaOut.model_validate(meta),
        bars=[serialize_bar(b) for b in result.bars],
        raw_pivots=[serialize_pivot(p) for p in result.raw_pivots],
        active_pivots=[serialize_pivot(p) for p in result.active_pivots],
        selected_anchor=(
            serialize_pivot(result.selected_anchor) if result.selected_anchor else None
        ),
        report=serialize_report(result.report),
        top_scenario=serialize_scenario(top) if top else None,
        top_scenario_layer1=top_scenario_layer1,
        scenario_counts=ScenarioCountsOut(
            total=len(scenarios),
            complete=n_complete,
            open=n_open,
        ),
        load_error=result.load_error,
    )


def serialize_theory_ref(ref: TheoryRef) -> TheoryRefOut:
    return TheoryRefOut(
        pages=list(ref.pages),
        concept=ref.concept,
        binding=ref.binding,
        note=ref.note,
    )


def serialize_target(t: Target) -> TargetOut:
    return TargetOut(
        name=t.name,
        price=t.price,
        type=t.type,
        theory_page=t.theory_page,
        derivation=humanize_family_codes(t.derivation),
    )


def serialize_target_set(ts: TargetSet | None) -> TargetSetOut | None:
    if ts is None:
        return None
    return TargetSetOut(
        confirmation_targets=[serialize_target(t) for t in ts.confirmation_targets],
        fib_flow_targets=[serialize_target(t) for t in ts.fib_flow_targets],
        invalidation=serialize_target(ts.invalidation),
    )


def serialize_bottleneck(b: BottleneckDiagnosis | None) -> BottleneckOut | None:
    if b is None:
        return None
    return BottleneckOut(
        slot_name=b.slot_name,
        slot_value=b.slot_value,
        dimension=b.dimension,
        is_dim_minimum=b.is_dim_minimum,
        is_overall_minimum=b.is_overall_minimum,
        gap_to_next=b.gap_to_next,
        intermediates=dict(b.intermediates),
        plain_explanation=b.plain_explanation,
        theory_ref=serialize_theory_ref(b.theory_ref),
    )


def serialize_confirmation_level(lv: ConfirmationLevel) -> ConfirmationLevelOut:
    return ConfirmationLevelOut(
        name=lv.name,
        condition=lv.condition,
        met=lv.met,
        triggered_at_bar=lv.triggered_at_bar,
        theory_page=lv.theory_page,
    )


def serialize_confirmation(
    c: ConfirmationReport | None,
) -> ConfirmationReportOut | None:
    if c is None:
        return None
    return ConfirmationReportOut(
        family=c.family,
        levels=[serialize_confirmation_level(lv) for lv in c.levels],
        is_applicable=c.is_applicable,
        not_applicable_reason=(
            NotApplicableReasonOut(
                text=c.not_applicable_reason.text,
                citation=c.not_applicable_reason.citation,
            )
            if c.not_applicable_reason is not None
            else None
        ),
        highest_met=c.highest_met,
    )


def serialize_price_move(m: PriceMove | None) -> PriceMoveOut | None:
    if m is None:
        return None
    return PriceMoveOut(
        label=m.label,
        price=m.price,
        pct_from_current=m.pct_from_current,
    )


def serialize_decision(d: DecisionSummary | None) -> DecisionSummaryOut | None:
    if d is None:
        return None
    return DecisionSummaryOut(
        current=serialize_price_move(d.current),
        target_low=serialize_price_move(d.target_low),
        target_high=serialize_price_move(d.target_high),
        invalidation=serialize_price_move(d.invalidation),
        risk_reward=d.risk_reward,
        direction=d.direction,
        horizon_bars=d.horizon_bars,
        bar_interval=d.bar_interval,
        horizon_human=d.horizon_human,
        stage=d.stage,
        open_wave_start=d.open_wave_start,
        open_wave_direction=d.open_wave_direction,
        wave_progress_pct=d.wave_progress_pct,
    )


def serialize_alternative(a: AlternativeBrief | None) -> AlternativeBriefOut | None:
    if a is None:
        return None
    return AlternativeBriefOut(
        family=a.family,
        family_label=a.family_label,
        target_low=serialize_price_move(a.target_low),
        target_high=serialize_price_move(a.target_high),
        invalidation=serialize_price_move(a.invalidation),
        direction=a.direction,
        stage=a.stage,
    )


def serialize_next_pattern(n: NextPattern) -> NextPatternOut:
    return NextPatternOut(
        link_type=n.link_type,
        next_families=list(n.next_families),
        link_band_near=n.link_band_near,
        link_band_far=n.link_band_far,
        theory_pages=list(n.theory_pages),
        rationale=n.rationale,
        link_wave_size=n.link_wave_size,
    )


def serialize_succession(s: SuccessionReport | None) -> SuccessionReportOut | None:
    if s is None:
        return None
    return SuccessionReportOut(
        family=s.family,
        is_terminal=s.is_terminal,
        next_patterns=[serialize_next_pattern(p) for p in s.next_patterns],
        note=s.note,
    )


def serialize_analysis_result(r: AnalysisResult) -> Layer1Response:
    return Layer1Response(
        scenario_id=r.scenario_id,
        bottleneck=serialize_bottleneck(r.bottleneck),
        confirmation=serialize_confirmation(r.confirmation),
        targets=serialize_target_set(r.targets),
        succession=serialize_succession(r.succession),
        decision=serialize_decision(r.decision),
        alternative=serialize_alternative(r.alternative),
        score_intermediates=dict(r.score_intermediates),
    )
