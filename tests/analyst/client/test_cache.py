from pathlib import Path

from analyst.client.cache import DiskCache, build_cache_key
from tests.analyst._helpers import make_scenario


def _fake_scenario():
    return make_scenario(
        score_components={"speed_cluster": 0.8, "leg_smoothness": 0.5},
    )


def test_build_cache_key_is_stable():
    sc = _fake_scenario()
    k1 = build_cache_key(sc, mode="explanation", prompt_version="v1",
                        model_id="qwen", rag_enabled=True)
    k2 = build_cache_key(sc, mode="explanation", prompt_version="v1",
                        model_id="qwen", rag_enabled=True)
    assert k1 == k2


def test_build_cache_key_differs_by_rag_flag():
    sc = _fake_scenario()
    k_on = build_cache_key(sc, mode="explanation", prompt_version="v1",
                          model_id="qwen", rag_enabled=True)
    k_off = build_cache_key(sc, mode="explanation", prompt_version="v1",
                           model_id="qwen", rag_enabled=False)
    assert k_on != k_off


def test_build_cache_key_differs_by_context():
    # The rendered data block (Layer-1 / chart) rides in `context`, so the same
    # scenario over revised bars (e.g. a newly-crossed confirmation trigger) must
    # not collide on the earlier narration.
    sc = _fake_scenario()
    k_a = build_cache_key(sc, mode="explanation", prompt_version="v1",
                          model_id="qwen", rag_enabled=True, context="awaiting confirmation")
    k_b = build_cache_key(sc, mode="explanation", prompt_version="v1",
                          model_id="qwen", rag_enabled=True, context="CONFIRMED")
    k_a2 = build_cache_key(sc, mode="explanation", prompt_version="v1",
                           model_id="qwen", rag_enabled=True, context="awaiting confirmation")
    assert k_a != k_b
    assert k_a == k_a2


def test_build_cache_key_differs_by_temperature():
    sc = _fake_scenario()
    k_cold = build_cache_key(sc, mode="explanation", prompt_version="v1",
                             model_id="qwen", rag_enabled=True,
                             temperature=0.2, seed=0)
    k_hot = build_cache_key(sc, mode="explanation", prompt_version="v1",
                            model_id="qwen", rag_enabled=True,
                            temperature=0.8, seed=0)
    assert k_cold != k_hot


def test_build_cache_key_differs_by_seed():
    sc = _fake_scenario()
    k_seed0 = build_cache_key(sc, mode="explanation", prompt_version="v1",
                              model_id="qwen", rag_enabled=True,
                              temperature=0.2, seed=0)
    k_seed1 = build_cache_key(sc, mode="explanation", prompt_version="v1",
                              model_id="qwen", rag_enabled=True,
                              temperature=0.2, seed=1)
    assert k_seed0 != k_seed1


def test_build_cache_key_omits_decoding_knobs_when_unspecified():
    sc = _fake_scenario()
    k = build_cache_key(sc, mode="explanation", prompt_version="v1",
                       model_id="qwen", rag_enabled=True)
    assert len(k) == 5


def test_disk_cache_round_trip(tmp_path: Path):
    cache = DiskCache(tmp_path)
    cache.put("k1", "value1")
    assert cache.get("k1") == "value1"
    assert cache.get("missing") is None


def test_disk_cache_drops_corrupt_entry(tmp_path: Path):
    cache = DiskCache(tmp_path)
    cache.put("k1", "value1")
    p = cache._path("k1")
    p.write_text("{not valid json")
    cache._mem.clear()
    assert cache.get("k1") is None
    assert not p.exists()


def test_disk_cache_put_is_atomic(tmp_path: Path):
    cache = DiskCache(tmp_path)
    cache.put("k1", "value1")
    files = list(tmp_path.iterdir())
    assert all(f.suffix != ".tmp" for f in files), files


def test_disk_cache_put_is_best_effort_on_write_failure(tmp_path: Path, monkeypatch):
    # Disk write failure (full/permissions) must not crash the request nor leak a
    # .tmp; the in-memory entry still serves the value.
    cache = DiskCache(tmp_path)

    def _boom(self, *a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", _boom)
    cache.put("k1", "value1")  # must not raise
    assert cache.get("k1") == "value1"  # mem entry kept
    assert not list(tmp_path.glob("*.tmp"))  # no orphaned temp


def test_disk_cache_evicts_oldest_when_over_budget(tmp_path: Path):
    cache = DiskCache(tmp_path, max_bytes=300)
    cache.put("k_old", "x" * 200)
    import os as _os
    p_old = cache._path("k_old")
    _os.utime(p_old, (0, 0))
    cache.put("k_new", "y" * 200)
    assert not p_old.exists()
    assert cache.get("k_old") is None
    assert cache.get("k_new") == "y" * 200


def test_disk_cache_max_bytes_zero_disables_eviction(tmp_path: Path):
    cache = DiskCache(tmp_path, max_bytes=0)
    for i in range(5):
        cache.put(f"k{i}", "x" * 1000)
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 5


def test_build_cache_key_handles_missing_span_start_time():
    class NoTimeScenario:
        family = "5W_TREND"
        pattern_kind = "X"
        score_components = {"speed_cluster": 0.5}

        class _Pv:
            time = None
            price = 100.0
        root = type("R", (), {"span_start": _Pv()})()

    sc = NoTimeScenario()
    kwargs = dict(mode="explanation", prompt_version="v1",
                  model_id="qwen", rag_enabled=True)
    # Missing span_start.time must not crash and must yield a stable key.
    assert build_cache_key(sc, **kwargs) == build_cache_key(sc, **kwargs)
