from __future__ import annotations

from dataclasses import dataclass

from ..types import HARD_TIMEOUT_MS, _Hypothesis
from .types import DiagnosticReport

__all__ = ["DiagnosticTracker", "build_diagnostic"]


def build_diagnostic(
    *,
    scenarios_empty: bool,
    timed_out: bool,
    timeout_at_segment: int,
    n_segments: int,
    first_divergence: int,
    last_alive: int,
    root_completed_at: int,
    timeout_ms: int = HARD_TIMEOUT_MS,
) -> DiagnosticReport:
    # Priority: timeout > root_done_early > 1-2 seg death > mid-parse death.
    diag = DiagnosticReport(
        first_divergence_index=first_divergence,
        last_alive_segment_index=last_alive,
    )
    if timed_out:
        diag.death_reason = "hard_timeout_exceeded"
        diag.suggested_action = (
            f"parser stopped at segment {timeout_at_segment} of {n_segments} "
            f"after {timeout_ms} ms — ลด BEAM_WIDTH / MAX_RECURSION_DEPTH "
            f"หรือใช้ช่วง segment ที่สั้นลง"
        )
        return diag
    if not scenarios_empty:
        return diag

    n_remaining = n_segments - 1
    if root_completed_at >= 0:
        diag.death_reason = "root_pattern_completed_but_segments_remain"
        diag.suggested_action = (
            f"root pattern จบที่ segment {root_completed_at} แต่ยังเหลือ segments "
            f"ถึง {n_remaining} — anchor เป็นจุดจบของ structure ที่เล็กเกินไป "
            f"ลอง anchor candidate ที่อยู่ก่อนหน้านี้ในกราฟ (ใหญ่กว่า)"
        )
    elif n_remaining >= 1 and last_alive <= 1:
        # Seed pool covers depth-1/2/3 + Link roots — dying so early ⇒ wrong anchor.
        diag.death_reason = "anchor_not_important_pivot"
        diag.suggested_action = (
            "ทุก hypothesis ตายภายใน 1-2 segments แรก แม้ลองครบทั้ง depth-1/2/3 "
            "Merging แล้ว — anchor นี้น่าจะไม่ใช่ Important High/Low จริง "
            "(อยู่กลาง structure) ลอง anchor candidate อื่นจาก list"
        )
    else:
        diag.death_reason = "rules_too_strict_or_pivot_noise"
        focus = f" (focus zone: รอบ segment {first_divergence})" if first_divergence >= 0 else ""
        diag.suggested_action = (
            f"hypotheses ตายระหว่าง parse ที่ segment {last_alive + 1}{focus} — "
            f"ลองปรับ Min-bars spacing หรือ ZigZag threshold เพื่อลด pivot noise"
        )
    return diag


@dataclass
class DiagnosticTracker:
    peak_count: int = 0
    peak_index: int = 0
    first_divergence: int = -1
    last_alive: int = 0
    root_completed_at: int = -1

    def observe_seed(self, seeds: list[_Hypothesis]) -> None:
        self.peak_count = len(seeds)
        self._scan_root_complete(seeds, 0)

    def observe_step(
        self,
        post_beam: list[_Hypothesis],
        segment_idx: int,
    ) -> None:
        if len(post_beam) > self.peak_count:
            self.peak_count = len(post_beam)
            self.peak_index = segment_idx
        elif (
            self.first_divergence < 0
            and segment_idx > self.peak_index
            and len(post_beam) < self.peak_count
        ):
            self.first_divergence = segment_idx

        if post_beam:
            self.last_alive = segment_idx
        elif self.first_divergence < 0:
            self.first_divergence = segment_idx

        self._scan_root_complete(post_beam, segment_idx)

    def _scan_root_complete(
        self,
        hyps: list[_Hypothesis],
        at_idx: int,
    ) -> None:
        if self.root_completed_at >= 0:
            return
        for h in hyps:
            if h.depth == 1 and h.top.is_complete:
                self.root_completed_at = at_idx
                return
