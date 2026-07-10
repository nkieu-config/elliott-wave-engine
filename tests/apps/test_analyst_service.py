"""Embedder gating in the composition root: the `grounding` extra is optional, so
enabling ANALYST_QA without it must degrade to a 503 route, never a 500 on encode()."""

from __future__ import annotations

import pytest

from apps.api.services import analyst_service


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("ANALYST_QA", raising=False)
    monkeypatch.delenv("ANALYST_GROUNDING_CHECK", raising=False)


def test_embedder_off_by_default(monkeypatch):
    monkeypatch.setattr(analyst_service, "_grounding_extra_installed", lambda: True)
    assert analyst_service._build_embedder() is None


def test_embedder_none_when_extra_missing(monkeypatch, caplog):
    monkeypatch.setenv("ANALYST_QA", "1")
    monkeypatch.setattr(analyst_service, "_grounding_extra_installed", lambda: False)
    assert analyst_service._build_embedder() is None
    assert "sentence-transformers is missing" in caplog.text


def test_grounding_check_also_needs_the_extra(monkeypatch):
    monkeypatch.setenv("ANALYST_GROUNDING_CHECK", "1")
    monkeypatch.setattr(analyst_service, "_grounding_extra_installed", lambda: False)
    assert analyst_service._build_embedder() is None


def test_embedder_built_when_requested_and_installed(monkeypatch):
    pytest.importorskip("sentence_transformers")
    monkeypatch.setenv("ANALYST_QA", "1")
    assert analyst_service._build_embedder() is not None


@pytest.mark.parametrize(
    ("qa_env", "installed", "expected"),
    [
        (None, True, False),
        ("1", False, False),
        ("1", True, True),
        (None, False, False),
    ],
)
def test_qa_enabled_setting(monkeypatch, qa_env, installed, expected):
    if qa_env is not None:
        monkeypatch.setenv("ANALYST_QA", qa_env)
    monkeypatch.setattr(
        analyst_service, "_grounding_extra_installed", lambda: installed
    )
    assert analyst_service.qa_enabled_setting() is expected


def test_grounding_extra_installed_matches_import():
    installed = analyst_service._grounding_extra_installed()
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        assert installed is False
    else:
        assert installed is True
