"""Public API. Import from here; submodule paths are internal and may move.

Names resolve lazily (PEP 562) so a bare import doesn't pull
the parser until a symbol is used.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

__version__ = "0.1.0"

# Public name -> defining submodule. Keep in sync with __all__ and TYPE_CHECKING.
_LAZY: dict[str, str] = {
    "run_pipeline": "engine.pipeline",
    "PipelineResult": "engine.pipeline",
    "BarRepository": "engine.data",
    "ScoringConfig": "engine.parser",
    "score_intermediates": "engine.parser.scoring",
    "Scenario": "engine.parser.output",
    "AnalysisReport": "engine.parser.output",
    "Bar": "engine.types",
    "Pivot": "engine.types",
    "Segment": "engine.types",
    "WaveNode": "engine.types",
    "ScaleMode": "engine.types",
    "TrendDir": "engine.types",
    "PatternKind": "engine.types",
}

# Literal (not ``[*_LAZY]``) so the linter sees these names are re-exported.
__all__ = [
    "__version__",
    "run_pipeline",
    "PipelineResult",
    "BarRepository",
    "ScoringConfig",
    "score_intermediates",
    "Scenario",
    "AnalysisReport",
    "Bar",
    "Pivot",
    "Segment",
    "WaveNode",
    "ScaleMode",
    "TrendDir",
    "PatternKind",
]


def __getattr__(name: str) -> object:
    module_path = _LAZY.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(module_path), name)
    globals()[name] = value  # cache; later access skips __getattr__
    return value


def __dir__() -> list[str]:
    return sorted(__all__)


if TYPE_CHECKING:
    # Re-export for type checkers; mirrors _LAZY. No runtime cost.
    from engine.data import BarRepository
    from engine.parser import ScoringConfig
    from engine.parser.output import AnalysisReport, Scenario
    from engine.parser.scoring import score_intermediates
    from engine.pipeline import PipelineResult, run_pipeline
    from engine.types import (
        Bar,
        PatternKind,
        Pivot,
        ScaleMode,
        Segment,
        TrendDir,
        WaveNode,
    )
