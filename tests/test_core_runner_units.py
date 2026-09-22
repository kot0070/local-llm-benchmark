"""Runner unit tests: think/options logic, status precedence, error mapping."""
import json

from bench import runner
from bench.ollama_client import OllamaError
from bench.types import Case, Profile, Request, Response


def prof(**kw):
    d = dict(tag="qwen3:8b", kind="chat", caps=["text"], think="toggle",
             ctx_max=40960,
             sampling={"thinking": {"temperature": 0.6},
                       "nonthinking": {"temperature": 0.7},
                       "default": {"temperature": 0.0}},
             adapters={}, stop=["<|im_end|>"], system=None,
             embed_prefix={}, profile_id="p1")
    d.update(kw)
    return Profile(**d)


def test_resolve_think_matrix():
    assert runner.resolve_think(prof(think="none"), "R1") == (None, [])
    assert runner.resolve_think(prof(think="toggle"), "R1")[0] is True
    assert runner.resolve_think(prof(think="toggle"), "R0")[0] is False
    think, flags = runner.resolve_think(prof(think="always"), "R0")
    assert think is True and flags == ["THINKING_FORCED"]
    assert runner.resolve_think(prof(think="always"), "R1") == (True, [])


def test_resolve_options_merge_and_stop():
    p = prof()
    meta = {"family": "TEXT"}
    req = Request(endpoint="chat", messages=[], options={"temperature": 0.9,
                                                         "stop": ["END"]})
    opts, stop = runner.resolve_options(p, meta, req, False, 256, 4096, 7)
    assert opts["temperature"] == 0.9  # test override wins
    assert opts["num_predict"] == 256 and opts["num_ctx"] == 4096
    assert opts["seed"] == 7
    assert stop == ["<|im_end|>", "END"]
    # thinking mode picks thinking sampling
    opts2, _ = runner.resolve_options(p, meta, Request(endpoint="chat"),
                                      True, 64, 4096, 1)
    assert opts2["temperature"] == 0.6
    # CODE family + thinking_code
    p3 = prof(sampling={"default": {"temperature": 0.1},
                        "thinking_code": {"temperature": 0.6}})
    opts3, _ = runner.resolve_options(p3, {"family": "CODE"},
                                      Request(endpoint="chat"), True, 64, 4096, 1)
    assert opts3["temperature"] == 0.6


def test_num_predict_think_extra():
    assert runner.num_predict_for({"num_predict": 384, "think_extra": 1024},
                                  False) == 384
    assert runner.num_predict_for({"num_predict": 384, "think_extra": 1024},
                                  True) == 1408


def test_apply_system_prepends_once():
    p = prof(system="SYS")
    r = Request(endpoint="chat",
                messages=[{"role": "user", "content": "hi"}])
    out = runner.apply_system(p, r)
    assert out.messages[0] == {"role": "system", "content": "SYS"}
    out2 = runner.apply_system(p, out)
    assert sum(1 for m in out2.messages if m["role"] == "system") == 1
    # generate requests untouched
    g = Request(endpoint="generate", prompt="hi")
    assert runner.apply_system(p, g) is g


def test_classify_exceptions():
    assert runner.classify_exception(TimeoutError("t"))[0] == "TIMEOUT"
    st, _, _ = runner.classify_exception(
        OllamaError("x", http_status=400, body="model context exceed limit"))
    assert st == "CONTEXT_OVERFLOW"
    st, _, _ = runner.classify_exception(
        OllamaError("x", http_status=500, body="CUDA error: out of memory"))
    assert st == "OOM_GPU"
    st, _, _ = runner.classify_exception(
        OllamaError("x", http_status=500, body="boom"), during_load=True)
    assert st == "MODEL_LOAD_ERROR"
    st, _, _ = runner.classify_exception(
        OllamaError("x", http_status=500, body="boom"))
    assert st == "MODEL_RUNTIME_ERROR"
    assert runner.classify_exception(ValueError("weird"))[0] == "HARNESS_ERROR"


def test_think_leak_stripping():
    c, t, leaked = runner.strip_think_leak("<think>hmm</think>answer", "prior")
    assert leaked and c == "answer" and "hmm" in t
    c2, t2, l2 = runner.strip_think_leak("plain answer", "")
    assert not l2 and c2 == "plain answer"


def test_model_size_ordering():
    tags = ["qwen3:14b", "functiongemma:270m", "qwen3:1.7b", "mistral-nemo:12b"]
    assert sorted(tags, key=runner.model_size_gb) == [
        "functiongemma:270m", "qwen3:1.7b", "mistral-nemo:12b", "qwen3:14b"]


def test_select_models_smoke_and_prefix(tmp_path):
    profiles = {t: prof(tag=t) for t in
                ["qwen3:1.7b", "functiongemma:270m", "nomic-embed-text:latest",
                 "granite3.2-vision:2b", "reader-lm:1.5b", "nuextract:3.8b",
                 "llama3.1:8b"]}
    assert runner.select_models(profiles, None, True) == [
        "qwen3:1.7b", "functiongemma:270m", "nomic-embed-text:latest",
        "granite3.2-vision:2b", "reader-lm:1.5b", "nuextract:3.8b"]
    assert runner.select_models(profiles, "qwen3", False) == ["qwen3:1.7b"]
    full = runner.select_models(profiles, None, False)
    assert full[0] == "functiongemma:270m"  # smallest first


def test_finalize_truncated_and_empty():
    import argparse
    _args = argparse.Namespace(run_id="r", budget_hours=0.1, smoke=False)
    import bench.registry as reg

    class FakeMod:
        META = {"version": "n1", "mode": "R0"}

        def validate(self, case, resp, profile):
            from bench.types import Verdict
            return Verdict(status="OK", sem=1.0, strict=1.0,
                           details={}, attribution="MODEL")

    _args = argparse.Namespace(run_id="r", budget_hours=0.1, smoke=False)

    class FakeCtx:
        modules = {"HOME-90": FakeMod()}
        args = _args
        digest_by_tag = {}
        ollama_version = "mock"

    case = Case(id="HOME-90-001", test_id="HOME-90")
    p = prof()
    meta = {"version": "n1", "mode": "R0"}
    inv = {"endpoint": "chat", "think": False}
    # truncated with content -> still validated for sem
    rec = runner.finalize_response(FakeCtx(), p, meta, case,
                                   Response(content="half", done_reason="length"),
                                   inv, [])
    assert rec["verdict"]["status"] == "OUTPUT_TRUNCATED"
    assert rec["verdict"]["sem"] == 1.0
    assert rec["verdict"]["strict"] == 0.0
    # empty -> EMPTY_OUTPUT
    rec2 = runner.finalize_response(FakeCtx(), p, meta, case,
                                    Response(content="", thinking="t",
                                             done_reason="stop"), inv, [])
    assert rec2["verdict"]["status"] == "EMPTY_OUTPUT"
    assert rec2["verdict"]["sub_reason"] == "EMPTY_AFTER_THINKING"
