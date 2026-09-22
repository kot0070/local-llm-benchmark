"""Test-module registry: discover bench/tests/home_*.py and index by META["id"]."""
from __future__ import annotations

import glob
import importlib.util
import os

REQUIRED_META_KEYS = ("id", "home", "family", "kind", "mode", "core_n", "timeout_s")
VALID_KINDS = {"chat", "vision", "embed", "tools_loop"}
VALID_MODES = {"R0", "R1", "-"}


def _load_module(path: str, modname: str):
    spec = importlib.util.spec_from_file_location(modname, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def discover(tests_dir: str | None = None) -> dict:
    """Discover home_*.py modules; return {META["id"]: module}.

    Raises ValueError on missing/invalid META or duplicate ids.
    """
    if tests_dir is None:
        tests_dir = os.path.join(os.path.dirname(__file__), "tests")
    pattern = os.path.join(tests_dir, "home_*.py")
    out: dict = {}
    for path in sorted(glob.glob(pattern)):
        base = os.path.splitext(os.path.basename(path))[0]
        mod = _load_module(path, f"bench.tests.{base}")
        meta = getattr(mod, "META", None)
        if not isinstance(meta, dict):
            raise ValueError(f"{path}: missing META dict")
        missing = [k for k in REQUIRED_META_KEYS if k not in meta]
        if missing:
            raise ValueError(f"{path}: META missing keys {missing}")
        if meta["kind"] not in VALID_KINDS:
            raise ValueError(f"{path}: bad kind {meta['kind']!r}")
        if meta["mode"] not in VALID_MODES:
            raise ValueError(f"{path}: bad mode {meta['mode']!r}")
        tid = meta["id"]
        if tid in out:
            raise ValueError(f"duplicate test id {tid}")
        req = getattr(mod, "load_cases", None)
        if meta["kind"] in ("chat", "vision") and not callable(getattr(mod, "build_request", None)):
            raise ValueError(f"{path}: chat/vision module needs build_request")
        if meta["kind"] in ("chat", "vision") and not callable(getattr(mod, "validate", None)):
            raise ValueError(f"{path}: chat/vision module needs validate")
        if meta["kind"] == "tools_loop" and not callable(getattr(mod, "run_case", None)):
            raise ValueError(f"{path}: tools_loop module needs run_case")
        if meta["kind"] == "embed" and not callable(getattr(mod, "run_embed", None)):
            raise ValueError(f"{path}: embed module needs run_embed")
        out[tid] = mod
    return out


def home_model_map(modules: dict) -> dict:
    """Return {model_tag: test_id} for the model's own HOME test."""
    return {mod.META["home"]: tid for tid, mod in modules.items() if mod.META.get("home")}
