"""tools_loop path + retry/attempt accounting vs the mock server."""
import argparse
import json
import os

import pytest

from bench import env as envmod
from bench import runner
from bench.ollama_client import OllamaClient
from bench.types import Case, Profile
from tests.mock_ollama import start

TOOLS_MOD = '''
from bench.types import Request, Verdict

META = dict(id="HOME-92", version="n1", title="fake tools", family="TOOLS",
            home="mock-tools:latest", kind="tools_loop", mode="R0",
            requires=["text"], num_predict=64, think_extra=0,
            num_ctx=8192, timeout_s=60, core_n=1, empty_ok=False)

def load_cases(fixtures_dir):
    import json, os
    with open(os.path.join(fixtures_dir, "cases.jsonl"), encoding="utf-8") as f:
        rows = [json.loads(ln) for ln in f if ln.strip()]
    from bench.types import Case
    return [Case(id=r["id"], test_id=r["test_id"], input=r.get("input", {}),
                 expected=r.get("expected")) for r in rows]

def run_case(case, profile, chat_fn):
    resp = chat_fn(Request(endpoint="chat", messages=[
        {"role": "user", "content": "TOOL weather in Paris?"}]))
    calls = resp.tool_calls or []
    ok = bool(calls) and calls[0].get("function", {}).get("name") == "get_weather"
    trace = [{"calls": calls}]
    if ok:
        return Verdict(status="OK", sem=1.0, strict=1.0,
                       details={"channel": "native"}, attribution="MODEL"), trace
    return Verdict(status="WRONG_ANSWER", sem=0.0, strict=0.0,
                   details={}, attribution="MODEL"), trace
'''


@pytest.fixture(scope="module")
def mock_url():
    srv, port = start(0)
    os.environ["BENCH_OLLAMA_URL"] = f"http://127.0.0.1:{port}"
    os.environ["BENCH_FAST_PREFLIGHT"] = "1"
    return f"http://127.0.0.1:{port}"


def _ctx(tmp_path):
    tdir = tmp_path / "t"
    tdir.mkdir(exist_ok=True)
    (tdir / "home_92.py").write_text(TOOLS_MOD, encoding="utf-8")
    fx = tmp_path / "fx" / "HOME-92"
    fx.mkdir(parents=True, exist_ok=True)
    with open(fx / "cases.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"id": "HOME-92-001", "test_id": "HOME-92",
                            "input": {}, "expected": {}}) + "\n")
    from bench import registry as registrymod
    modules = registrymod.discover(str(tdir))
    args = argparse.Namespace(run_id="tools", budget_hours=2.0, smoke=False)
    import time
    import bench.store as storemod
    run_dir = str(tmp_path / "res")
    os.makedirs(run_dir, exist_ok=True)
    ctx = runner.Ctx(args, run_dir, modules,
                     {"mock-tools:latest": Profile(
                         tag="mock-tools:latest", kind="chat", caps=["text"],
                         think="none", ctx_max=8192, sampling={},
                         profile_id="mock.tools.v1")},
                     {}, OllamaClient(), storemod.Store(run_dir),
                     time.time() + 3600.0)
    return ctx, modules


def test_tools_loop_native_calls(mock_url, tmp_path, monkeypatch):
    monkeypatch.setattr(envmod, "nvidia_snapshot", lambda: None)
    ctx, modules = _ctx(tmp_path)
    module = modules["HOME-92"]
    cases = module.load_cases(str(tmp_path / "fx" / "HOME-92"))
    think, flags = runner.resolve_think(ctx.profiles["mock-tools:latest"], "R0")
    rec = runner.run_tools_case(ctx, module, ctx.profiles["mock-tools:latest"],
                                dict(module.META), cases[0], think, flags)
    assert rec["verdict"]["status"] == "OK"
    assert rec["verdict"]["sem"] == 1.0
    assert rec["response"]["trace"][0]["calls"][0]["function"]["name"] == "get_weather"


def test_retry_records_attempt_then_runtime_error(mock_url, tmp_path,
                                                  monkeypatch):
    monkeypatch.setattr(envmod, "nvidia_snapshot", lambda: None)
    monkeypatch.setattr(runner.time, "sleep", lambda *a, **k: None)
    ctx, modules = _ctx(tmp_path)
    profile = ctx.profiles["mock-tools:latest"]
    meta = {"version": "n1", "mode": "R0", "num_predict": 64, "think_extra": 0,
            "num_ctx": 4096, "timeout_s": 10}
    case = Case(id="HTTP500-boom", test_id="HOME-92", input={"text": "HTTP500 x"})
    import types
    chat_mod = types.SimpleNamespace(
        META=dict(id="HOME-92", version="n1", mode="R0", num_predict=64,
                  think_extra=0, num_ctx=4096, timeout_s=10),
        build_request=lambda case, profile: __import__(
            "bench.types", fromlist=["Request"]).Request(
            endpoint="chat",
            messages=[{"role": "user", "content": "HTTP500 x"}],
            options={}))
    ctx.modules["HOME-92"] = chat_mod
    rec = runner.run_chat_case(ctx, chat_mod, profile, chat_mod.META, case,
                               None, [])
    assert rec["verdict"]["status"] == "MODEL_RUNTIME_ERROR"
    assert rec["attempt"] == 1  # one retry performed
    assert rec["response"]["error"]


def test_ctx_overflow_no_retry(mock_url, tmp_path, monkeypatch):
    monkeypatch.setattr(envmod, "nvidia_snapshot", lambda: None)
    monkeypatch.setattr(runner.time, "sleep", lambda *a, **k: None)
    ctx, modules = _ctx(tmp_path)
    profile = ctx.profiles["mock-tools:latest"]
    import bench.types as T
    chat_mod = type("M", (), {})()
    chat_mod.META = dict(id="HOME-92", version="n1", mode="R0", num_predict=64,
                         think_extra=0, num_ctx=4096, timeout_s=10)
    chat_mod.build_request = lambda case, profile: T.Request(
        endpoint="chat", messages=[{"role": "user", "content": "CTX_OVERFLOW x"}],
        options={})
    ctx.modules["HOME-92"] = chat_mod
    case = Case(id="CTX_OVERFLOW-x", test_id="HOME-92")
    rec = runner.run_chat_case(ctx, chat_mod, profile, chat_mod.META, case,
                               None, [])
    assert rec["verdict"]["status"] == "CONTEXT_OVERFLOW"
    assert rec["attempt"] == 0  # not retryable
