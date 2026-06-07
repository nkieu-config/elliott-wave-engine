from __future__ import annotations

from typing import Any, Protocol


class LLMClient(Protocol):
    model_id: str

    def complete(
        self, messages: list[dict[str, str]], *, format: Any | None = None
    ) -> str:
        ...
