from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfirmationLevel:
    name: str
    condition: str
    met: bool
    triggered_at_bar: int | None
    theory_page: int


@dataclass(frozen=True)
class NotApplicableReason:
    text: str
    citation: int | None


@dataclass(frozen=True)
class ConfirmationReport:
    family: str
    levels: tuple[ConfirmationLevel, ...] = ()
    _not_applicable_reason: NotApplicableReason | None = None

    @classmethod
    def not_applicable(
        cls, family: str, reason: str, citation: int | None,
    ) -> ConfirmationReport:
        return cls(
            family=family,
            levels=(),
            _not_applicable_reason=NotApplicableReason(text=reason, citation=citation),
        )

    @property
    def is_applicable(self) -> bool:
        return self._not_applicable_reason is None

    @property
    def not_applicable_reason(self) -> NotApplicableReason | None:
        return self._not_applicable_reason

    @property
    def highest_met(self) -> str | None:
        met = [lv for lv in self.levels if lv.met]
        return met[-1].name if met else None
