from __future__ import annotations

import pytest

from tests.engine.parser.scoring._helpers import reset_pivot_counter


@pytest.fixture(autouse=True)
def _reset_pivot_counter() -> None:
    # Reset module-global pivot counter per test for cross-subpackage isolation.
    reset_pivot_counter()
