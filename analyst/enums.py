# Two NOT-interchangeable variants (fallback is load-bearing for the wire format):
# enum_value → str(x) fallback for always-string fields; enum_value_or_none →
# None fallback for optional fields that serialize to JSON null when absent.

from __future__ import annotations

from typing import Any


def enum_value(x: Any) -> Any:
    return x.value if hasattr(x, "value") else str(x)


def enum_value_or_none(x: Any) -> Any | None:
    return x.value if x and hasattr(x, "value") else None
