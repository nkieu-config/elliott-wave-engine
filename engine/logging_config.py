from __future__ import annotations

import logging
import os
from typing import Final

# Env: EWL_LOG_LEVEL/EWL_LOG_FORMAT/EWL_LOG_FILE. Idempotent (safe to call repeatedly).
_DEFAULT_FORMAT: Final = (
    "%(asctime)s %(levelname)-7s %(name)s — %(message)s"
)
_DEFAULT_LEVEL: Final = "INFO"

_CONFIGURED_ATTR: Final = "_ewl_logging_configured"


def configure_logging(*, force: bool = False) -> None:
    root = logging.getLogger()
    if not force and getattr(root, _CONFIGURED_ATTR, False):
        return

    level_name = os.environ.get("EWL_LOG_LEVEL", _DEFAULT_LEVEL).upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt = os.environ.get("EWL_LOG_FORMAT", _DEFAULT_FORMAT)

    formatter = logging.Formatter(fmt)

    # Remove only our own handlers; leave third-party alone.
    for h in list(root.handlers):
        if getattr(h, "_ewl_owned", False):
            root.removeHandler(h)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console._ewl_owned = True  # type: ignore[attr-defined]
    root.addHandler(console)

    log_file = os.environ.get("EWL_LOG_FILE")
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler._ewl_owned = True  # type: ignore[attr-defined]
        root.addHandler(file_handler)

    root.setLevel(level)
    setattr(root, _CONFIGURED_ATTR, True)
