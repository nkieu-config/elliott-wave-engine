from __future__ import annotations


def test_public_symbols_are_importable_from_analyst() -> None:
    import analyst

    for name in analyst.__all__:
        assert hasattr(analyst, name), (
            f"analyst/__init__.py declares __all__ entry {name!r} but the "
            "symbol is not exported"
        )


def test_canonical_public_symbols_are_present() -> None:
    import analyst

    required = {
        "Analyst", "analyze", "build_analyst",
        "OllamaClient",
        "Chunk", "Embedder", "PIPELINE_FINGERPRINT",
        "AnalysisOutput", "AnalysisResult",
        "BottleneckDiagnosis", "TargetSet",
        "GLOSSARY", "concept_for_page", "trendline_at",
    }
    missing = required - set(analyst.__all__)
    assert not missing, f"analyst.__all__ is missing required symbols: {missing}"


def test_dashboard_uses_public_surface_only() -> None:
    import pathlib
    import re

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    dashboard_root = repo_root / "dashboard"
    private_import_re = re.compile(r"^\s*from\s+analyst\.[^\s]+\s+import\b")

    offenders = []
    for py in dashboard_root.rglob("*.py"):
        for lineno, line in enumerate(py.read_text().splitlines(), start=1):
            if private_import_re.match(line):
                offenders.append(f"{py.relative_to(repo_root)}:{lineno}  {line.strip()}")
    assert not offenders, (
        "dashboard files reach into analyst's private modules — route via "
        "analyst.__init__ instead:\n  " + "\n  ".join(offenders)
    )
