"""Optional performance instrumentation.

Disabled by default. Enable via the ``--perf`` CLI flag (or ``perf.enable()``
for tests/benchmarks). When enabled, instrumented code paths emit

    [PERF] <label>: <elapsed_ms> ms

to stderr. When disabled the cost is a single module-level bool read per
call site, so it is safe to leave the timers in production code.
"""

from __future__ import annotations

import sys
import time
from contextlib import contextmanager

_ENABLED = False


def enable(value: bool = True) -> None:
    """Turn performance instrumentation on or off globally."""
    global _ENABLED
    _ENABLED = bool(value)


def is_enabled() -> bool:
    return _ENABLED


@contextmanager
def timed(label: str):
    """Time a scoped block.

    Emits ``[PERF] <label>: <ms> ms`` on exit when instrumentation is on.
    No-op otherwise. Works for both sync and async scopes — the context
    manager itself doesn't need to be async-aware because it's used with
    ``with``, not ``async with``.
    """
    if not _ENABLED:
        yield
        return
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt_ms = (time.perf_counter() - t0) * 1000.0
        print(f"[PERF] {label}: {dt_ms:8.2f} ms", file=sys.stderr, flush=True)


def log(label: str, ms: float) -> None:
    """Record a timing measured elsewhere (e.g. via a callback)."""
    if _ENABLED:
        print(f"[PERF] {label}: {ms:8.2f} ms", file=sys.stderr, flush=True)


def _install_trame_rca_hooks():
    """Monkey-patch trame_rca so encode + push phases show up under --perf.

    Installed once at module import. Wrappers check _ENABLED per-call; no
    overhead when perf is off beyond the bool test.

    Emits:
        [PERF] rca.encode.<encoder>: <ms> ms    (per encode, thread-pool)
        [PERF] rca.push.<area>:     <ms> ms    (per websocket push)
    """
    try:
        from trame_rca.utils import RcaEncoder, RcaViewAdapter
    except ImportError:
        return

    _orig_encode = RcaEncoder.encode

    def _timed_encode(self, np_image, cols, rows, quality):
        if not _ENABLED:
            return _orig_encode(self, np_image, cols, rows, quality)
        t0 = time.perf_counter()
        try:
            return _orig_encode(self, np_image, cols, rows, quality)
        finally:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            print(
                f"[PERF] rca.encode.{self.value}: {dt_ms:8.2f} ms",
                file=sys.stderr,
                flush=True,
            )

    RcaEncoder.encode = _timed_encode

    _orig_push = RcaViewAdapter.push

    def _timed_push(self, content, meta):
        if not _ENABLED:
            return _orig_push(self, content, meta)
        t0 = time.perf_counter()
        try:
            return _orig_push(self, content, meta)
        finally:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            print(
                f"[PERF] rca.push.{self.area_name}: {dt_ms:8.2f} ms",
                file=sys.stderr,
                flush=True,
            )

    RcaViewAdapter.push = _timed_push


# Install RCA hooks eagerly at import. The wrappers are near-free when
# instrumentation is disabled (one bool check per call site).
_install_trame_rca_hooks()
