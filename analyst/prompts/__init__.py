from __future__ import annotations

from analyst.prompts import (
    differentiator,
    explanation,
    scenario_outlook,
    slot_focus,
)
from analyst.prompts.repair import build_repair_prompt
from analyst.prompts.system import PROMPT_VERSION, SYSTEM_PROMPT

_MODE_PROMPTS = {
    "explanation": explanation.USER_PROMPT,
    "slot_focus": slot_focus.USER_PROMPT,
    "differentiator": differentiator.USER_PROMPT,
    "scenario_outlook": scenario_outlook.USER_PROMPT,
}


def build_prompt(mode: str, layer1_md: str, theory_md: str) -> tuple[str, str]:
    if mode not in _MODE_PROMPTS:
        raise ValueError(f"Unknown mode: {mode!r}")
    user_prompt = (
        f"[LAYER-1 DATA]\n{layer1_md}\n\n"
        f"[THEORY REFS]\n{theory_md}\n\n"
        f"[USER]\n{_MODE_PROMPTS[mode]}"
    )
    return SYSTEM_PROMPT, user_prompt


__all__ = ["PROMPT_VERSION", "build_prompt", "build_repair_prompt"]
