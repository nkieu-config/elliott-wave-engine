from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_MAX_BYTES = 256 * 1024 * 1024


def build_cache_key(
    sc: Any,
    mode: str,
    prompt_version: str,
    model_id: str,
    rag_enabled: bool,
    *,
    temperature: float | None = None,
    seed: int | None = None,
    context: str = "",
) -> tuple:
    # Content-derived hash (§5.7) — survives parser UUID regen. Key widens only
    # when temperature/seed supplied, so legacy entries don't collide. `context`
    # folds in the rendered prompt data block (Layer-1 / chart) so bars/scale_mode
    # changes that leave score_components untouched still invalidate the entry.
    components = sc.score_components or {}
    span_start = getattr(sc.root, "span_start", None)
    time_val = getattr(span_start, "time", None) if span_start else None
    time_str = time_val.isoformat() if time_val is not None else "?"
    price_str = (
        f"{getattr(span_start, 'price', '?')}" if span_start else "?"
    )
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    payload = (
        f"{sc.family}|"
        f"{getattr(sc, 'pattern_kind', '?')}|"
        f"{sorted(components.items())}|"
        f"{time_str}|"
        f"{price_str}|"
        f"{context_hash}"
    )
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    base = (h, mode, prompt_version, model_id, rag_enabled)
    if temperature is None and seed is None:
        return base
    return (*base, temperature, seed)


class DiskCache:
    # max_bytes=0 disables eviction (legacy unbounded mode used by tests).
    def __init__(self, root: Path, max_bytes: int = _DEFAULT_MAX_BYTES):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self._mem: dict[str, Any] = {}
        # Shared across worker threads. Non-reentrant: only get/put acquire it —
        # eviction helpers run under put's hold, must not re-acquire.
        self._lock = threading.Lock()

    def _path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / f"{h}.json"

    def get(self, key: Any) -> Any | None:
        k = str(key)
        with self._lock:
            if k in self._mem:
                # Touch so repeated reads survive eviction.
                p = self._path(k)
                if p.exists():
                    _touch(p)
                return self._mem[k]
            p = self._path(k)
            if not p.exists():
                return None
            try:
                value = json.loads(p.read_text())["value"]
            except (json.JSONDecodeError, KeyError, OSError) as e:
                # Partial write / schema drift — drop and miss.
                logger.warning("DiskCache: dropping corrupt entry %s (%s)", p, e)
                with contextlib.suppress(OSError):
                    p.unlink()
                return None
            self._mem[k] = value
            _touch(p)
            return value

    def put(self, key: Any, value: Any) -> None:
        # Tempfile + rename — kill mid-write can't leave a torn file.
        k = str(key)
        p = self._path(k)
        tmp = p.with_suffix(p.suffix + ".tmp")
        blob = json.dumps({"value": value})  # serialize outside the lock
        with self._lock:
            self._mem[k] = value
            try:
                tmp.write_text(blob)
                tmp.replace(p)
            except OSError as e:
                # Best-effort: keep the mem entry; clean the tmp (eviction skips *.tmp).
                logger.warning("DiskCache: write failed for %s (%s)", p, e)
                with contextlib.suppress(OSError):
                    tmp.unlink()
                return
            if self.max_bytes > 0:
                self._evict_if_over_budget(protect=p)

    def _evict_if_over_budget(self, *, protect: Path) -> None:
        # protect = entry just written — never evict it (would cause put/get miss).
        # stat once, and skip a file a concurrent write/clear unlinked mid-scan.
        entries = []
        for f in self.root.glob("*.json"):
            try:
                st = f.stat()
            except OSError:
                continue
            entries.append((st.st_mtime, st.st_size, f))
        total = sum(size for _, size, _ in entries)
        if total <= self.max_bytes:
            return
        entries.sort(key=lambda t: t[0])
        for _mtime, size, path in entries:
            if total <= self.max_bytes:
                break
            if path == protect:
                continue
            try:
                path.unlink()
                total -= size
                # Drop mem mirror so subsequent get() doesn't mask eviction.
                self._forget_mem_for_path(path)
            except OSError as e:
                logger.warning(
                    "DiskCache: failed to evict %s (%s)", path, e,
                )
                continue
        if total > self.max_bytes:
            logger.warning(
                "DiskCache: still %d bytes after eviction (budget %d); "
                "the just-written entry is being protected.",
                total, self.max_bytes,
            )

    def _forget_mem_for_path(self, path: Path) -> None:
        target_stem = path.stem
        for k in list(self._mem):
            if self._path(k).stem == target_stem:
                self._mem.pop(k, None)
                return


def _touch(path: Path) -> None:
    with contextlib.suppress(OSError):
        os.utime(path, None)
