from __future__ import annotations

import logging

import pytest

from engine.logging_config import configure_logging


@pytest.fixture(autouse=True)
def _reset_root_logger():
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    saved_flag = getattr(root, "_ewl_logging_configured", None)
    try:
        root.handlers = []
        if hasattr(root, "_ewl_logging_configured"):
            delattr(root, "_ewl_logging_configured")
        yield
    finally:
        root.handlers = saved_handlers
        root.setLevel(saved_level)
        if saved_flag is not None:
            root._ewl_logging_configured = saved_flag


def test_configure_installs_one_handler() -> None:
    configure_logging()
    root = logging.getLogger()
    owned = [h for h in root.handlers if getattr(h, "_ewl_owned", False)]
    assert len(owned) == 1


def test_configure_is_idempotent() -> None:
    configure_logging()
    configure_logging()
    configure_logging()
    root = logging.getLogger()
    owned = [h for h in root.handlers if getattr(h, "_ewl_owned", False)]
    assert len(owned) == 1


def test_force_reinstalls_handler() -> None:
    configure_logging()
    configure_logging(force=True)
    root = logging.getLogger()
    owned = [h for h in root.handlers if getattr(h, "_ewl_owned", False)]
    assert len(owned) == 1


def test_level_read_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EWL_LOG_LEVEL", "DEBUG")
    configure_logging(force=True)
    assert logging.getLogger().level == logging.DEBUG


def test_unknown_level_falls_back_to_info(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EWL_LOG_LEVEL", "verbose")
    configure_logging(force=True)
    assert logging.getLogger().level == logging.INFO


def test_file_handler_added_when_env_set(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    log_path = tmp_path / "ewl.log"
    monkeypatch.setenv("EWL_LOG_FILE", str(log_path))
    configure_logging(force=True)
    root = logging.getLogger()
    owned = [h for h in root.handlers if getattr(h, "_ewl_owned", False)]
    file_handlers = [h for h in owned if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 1
    assert file_handlers[0].baseFilename == str(log_path)
