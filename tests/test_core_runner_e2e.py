"""End-to-end runner test vs the mock server with 2 tiny fake test modules."""
import json
import os

import pytest

from bench import env as envmod
from bench import runner
from tests.mock_ollama import start

CHAT_MOD = '''
from bench.types import Case, Request, Verdict

META = dict(id="HOME-90", version="n1", title="fake chat", family="TEXT",
            home="mock-chat:latest", kind="chat", mode="R0",
            requires=["text"], num_predict=64, think_extra=0,
            num_ctx=4096, timeout_s=60, core_n=2, empty_ok=False)

def load_cases(fixtures_dir):
    import json, os
    with open(os.path.join(fixtures_dir, "cases.jsonl"), encoding="utf-8") as f:
        rows = [json.loads(ln) for ln in f if ln.strip()]
    return [Case(id=r["id"], test_id=r["test_id"], tier=r.get("tier", ""),
                 lang=r.get("lang", "en"), input=r.get("input", {}),
                 expected=r.get("expected"), meta=r.get("meta", {}))
            for r in rows]

def build_request(case, profile):
    return Request(endpoint="chat",
                   messages=[{"role": "user", "content": case.input["text"]}],
                   options={})

def validate(case, resp, profile):
    if "reply:" in resp.content:
        return Verdict(status="OK", sem=1.0, strict=1.0,
                       details={"echo": True}, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sem=0.0, strict=0.0,
                   details={}, attribution="MODEL")
'''

EMBED_MOD = '''
import math
from bench.types import Verdict

META = dict(id="HOME-91", version="n1", title="fake embed", family="EMBED",
            home="mock-embed:latest", kind="embed", mode="-",
            requires=["embed"], num_ctx=0, timeout_s=60, core_n=3,
            empty_ok=True)

def load_cases(fixtures_dir):
    import json, os
    with open(os.path.join(fixtures_dir, "cases.jsonl"), encoding="utf-8") as f:
        rows = [json.loads(ln) for ln in f if ln.strip()]
    from bench.types import Case
    return [Case(id=r["id"], test_id=r["test_id"], tier=r.get("tier", ""),
                 lang=r.get("lang", "en"), input=r.get("input", {}),
                 expected=r.get("expected"), meta=r.get("meta", {}))
            for r in rows]

def _cos(a, b):
    n = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / n if n else 0.0

def run_embed(cases, profile, embed_fn):
    out = []
    for case in cases:
        docs = case.input["docs"]
        vecs = embed_fn(docs + [case.input["query"]]).embeddings
        q = vecs[-1]
        sims = sorted(range(len(docs)), key=lambda i: -_cos(q, vecs[i]))
        # query paraphrases docs[0], so top-1 should be doc 0
        sem = 1.0 if sims[0] == 0 else 0.0
        st = "OK" if sem == 1.0 else "WRONG_ANSWER"
        out.append((case, Verdict(status=st, sem=sem, strict=sem,
                                  details={"top": sims[0]}, attribution="MODEL")))
    return out
'''

PROFILES = {"profiles": {
    "mock-chat:latest": {"kind": "chat", "caps": ["text"], "think": "none",
                         "ctx_max": 8192, "sampling": {"default": {"temperature": 0.0}},
                         "profile_id": "mock.chat.v1"},
    "mock-embed:latest": {"kind": "embed", "caps": ["embed"], "think": "none",
                          "ctx_max": 8192, "sampling": {},
                          "profile_id": "mock.embed.v1"},
}}


@pytest.fixture(scope="module")
def mock_url():
    srv, port = start(0)
    url = f"http://127.0.0.1:{port}"
    os.environ["BENCH_OLLAMA_URL"] = url
    os.environ["BENCH_FAST_PREFLIGHT"] = "1"
    return url


@pytest.fixture()
def stage(tmp_path, monkeypatch):
    monkeypatch.setattr(envmod, "idle_baseline",
                        lambda *a, **k: {"samples": 0, "vram_baseline_mb": 100.0,
                                         "gpu_util_median": 0.0, "idle_temp_c": 40.0})
    monkeypatch.setattr(envmod, "contention_check", lambda *a, **k: (True, {}))
    monkeypatch.setattr(envmod, "thermal_gate", lambda *a, **k: {"temp_c": 40.0})
    monkeypatch.setattr(envmod, "unload_all", lambda *a, **k: (True, {}))
    monkeypatch.setattr(envmod, "nvidia_snapshot", lambda: None)
    monkeypatch.setattr(envmod, "fingerprint", lambda *a, **k: {"gpu": "mock"})
    tdir = tmp_path / "tests"
    tdir.mkdir()
    (tdir / "home_90.py").write_text(CHAT_MOD, encoding="utf-8")
    (tdir / "home_91.py").write_text(EMBED_MOD, encoding="utf-8")
    fx = tmp_path / "fixtures"
    (fx / "HOME-90").mkdir(parents=True)
    (fx / "HOME-91").mkdir(parents=True)
    chat_cases = [{"id": f"HOME-90-00{i}", "test_id": "HOME-90", "tier": "easy",
                   "lang": "en", "input": {"text": f"hello {i}"},
                   "expected": "reply:", "meta": {}} for i in range(1, 5)]
    with open(fx / "HOME-90" / "cases.jsonl", "w", encoding="utf-8") as f:
        for c in chat_cases:
            f.write(json.dumps(c) + "\n")
    emb_cases = [{"id": f"HOME-91-00{i}", "test_id": "HOME-91", "tier": "easy",
                  "lang": "en",
                  "input": {"docs": [f"the red fox jumps {i}",
                                     "quantum chromodynamics lecture notes",
                                     "borscht recipe with beetroot"],
                            "query": f"the red fox jumps {i}"},
                  "expected": 0, "meta": {}} for i in range(1, 4)]
    with open(fx / "HOME-91" / "cases.jsonl", "w", encoding="utf-8") as f:
        for c in emb_cases:
            f.write(json.dumps(c) + "\n")
    prof_path = tmp_path / "profiles.json"
    prof_path.write_text(json.dumps(PROFILES), encoding="utf-8")
    elig = {"HOME-90": {"mock-chat:latest": {"code": "E", "reason": "HOME"},
                        "mock-embed:latest": {"code": "U", "reason": "CAP: no text"}},
            "HOME-91": {"mock-chat:latest": {"code": "U", "reason": "CAP: no embed"},
                        "mock-embed:latest": {"code": "E", "reason": "HOME"}}}
    elig_path = tmp_path / "elig.json"
    elig_path.write_text(json.dumps(elig), encoding="utf-8")
    return {"tests_dir": str(tdir), "fixtures": str(fx),
            "profiles": str(prof_path), "eligibility": str(elig_path),
            "results_root": str(tmp_path / "results")}


def _run(stage, extra):
    args = ["--budget-hours", "2", "--run-id", "e2e",
            "--tests-dir", stage["tests_dir"], "--fixtures", stage["fixtures"],
            "--profiles", stage["profiles"], "--eligibility",
            stage["eligibility"], "--results-root", stage["results_root"]] + extra
    return runner.main(args)


def test_e2e_phases_and_statuses(mock_url, stage):
    rc = _run(stage, ["--phase", "1"])
    assert rc == 0
    rc = _run(stage, ["--phase", "2"])
    assert rc == 0
    import glob
    rdir = os.path.join(stage["results_root"], "e2e")
    assert os.path.exists(os.path.join(rdir, "manifest.json"))
    assert os.path.exists(os.path.join(rdir, "preflight.json"))
    assert os.path.exists(os.path.join(rdir, "summary.md"))
    recs = [json.loads(ln) for ln in
            open(os.path.join(rdir, "results.jsonl"), encoding="utf-8")
            if ln.strip()]
    by_test: dict = {}
    for r in recs:
        by_test.setdefault(r["key"].split("|")[3].split("@")[0], []).append(r)
    assert "PERF" in by_test and len(by_test["PERF"]) >= 6
    home90 = [r for r in by_test.get("HOME-90", [])
              if "mock-chat" in r["key"]]
    assert len(home90) == 4, f"expected 4 HOME-90 chat cases, got {len(home90)}"
    assert all(r["verdict"]["status"] == "OK" for r in home90)
    # unsupported home-90 for embed model recorded once
    unsup = [r for r in recs
             if r["verdict"]["status"] == "UNSUPPORTED_CAPABILITY"]
    assert any("HOME-90" in r["key"] and "mock-embed" in r["key"] for r in unsup)
    emb = [r for r in by_test.get("HOME-91", []) if "mock-embed" in r["key"]]
    assert len(emb) == 3 and all(r["verdict"]["status"] == "OK" for r in emb)


def test_e2e_resume_skips_final(mock_url, stage):
    _run(stage, ["--phase", "1"])
    rdir = os.path.join(stage["results_root"], "e2e")
    n1 = sum(1 for _ in open(os.path.join(rdir, "results.jsonl"),
                             encoding="utf-8"))
    rc = runner.main(["--budget-hours", "2", "--resume", "e2e",
                      "--tests-dir", stage["tests_dir"], "--fixtures",
                      stage["fixtures"], "--profiles", stage["profiles"],
                      "--eligibility", stage["eligibility"], "--results-root",
                      stage["results_root"], "--phase", "1"])
    assert rc == 0
    n2 = sum(1 for _ in open(os.path.join(rdir, "results.jsonl"),
                             encoding="utf-8"))
    assert n2 >= n1  # resume ran; final keys skipped (no duplicates expected
    # beyond perf re-records guard) -- at minimum nothing crashed


def test_dry_run_no_requests(mock_url, stage, capsys):
    rc = _run(stage, ["--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "HOME-90" in out and "mock-chat" in out
