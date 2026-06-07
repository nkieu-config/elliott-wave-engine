from pathlib import Path

from analyst._fingerprint import (
    _ANALYST_ROOT,
    _EXCLUDED_PARTS,
    PIPELINE_FINGERPRINT,
    _compute_fingerprint,
)


def test_fingerprint_is_a_short_hex_string():
    assert isinstance(PIPELINE_FINGERPRINT, str)
    assert len(PIPELINE_FINGERPRINT) == 16
    int(PIPELINE_FINGERPRINT, 16)


def test_fingerprint_is_deterministic():
    assert _compute_fingerprint() == _compute_fingerprint()
    assert _compute_fingerprint() == PIPELINE_FINGERPRINT


def test_exclusion_list_stays_minimal():
    assert frozenset({"eval", "__pycache__", ".cache"}) == _EXCLUDED_PARTS


def test_pipeline_edit_shifts_the_fingerprint(tmp_path: Path, monkeypatch):
    import shutil

    mirror = tmp_path / "analyst"
    shutil.copytree(_ANALYST_ROOT, mirror, ignore=shutil.ignore_patterns(
        "__pycache__", ".cache", "data", "*.npy",
    ))

    import analyst._fingerprint as fp
    monkeypatch.setattr(fp, "_ANALYST_ROOT", mirror)

    digest_before = fp._compute_fingerprint()

    gate_path = mirror / "client" / "gate.py"
    gate_path.write_text(gate_path.read_text() + "\n# fingerprint test edit\n")

    digest_after = fp._compute_fingerprint()
    assert digest_before != digest_after, (
        "Editing analyst/client/gate.py did NOT shift the fingerprint — "
        "the narration cache would silently serve pre-edit results."
    )


def test_excluded_file_does_not_shift_the_fingerprint(
    tmp_path: Path, monkeypatch,
):
    import shutil

    mirror = tmp_path / "analyst"
    shutil.copytree(_ANALYST_ROOT, mirror, ignore=shutil.ignore_patterns(
        "__pycache__", ".cache", "data", "*.npy",
    ))
    eval_dir = mirror / "eval"
    eval_dir.mkdir(exist_ok=True)
    eval_file = eval_dir / "scratch.py"
    eval_file.write_text("# initial\n")

    import analyst._fingerprint as fp
    monkeypatch.setattr(fp, "_ANALYST_ROOT", mirror)

    digest_before = fp._compute_fingerprint()
    eval_file.write_text("# changed\n")
    digest_after = fp._compute_fingerprint()
    assert digest_before == digest_after, (
        "Editing a file under an excluded directory DID shift the "
        "fingerprint — the exclusion no longer holds."
    )
