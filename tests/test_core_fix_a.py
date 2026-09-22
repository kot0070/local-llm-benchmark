"""FIX_A unit tests: audit findings for TASK_A core harness."""
import argparse
import json
import os
import time

from bench import env as envmod
from bench import runner
from bench.ollama_client import OllamaError
from bench.types import Case, Profile, Response


def _prof(**kw):
    d = dict(tag="m", kind="chat", caps=["text"], think="none",
             ctx_max=4096, sampling={"default": {"temperature": 0.0}},
             adapters={}, stop=[], system=None, embed_prefix={},
             profile_id="p")
    d.update(kw)
    return Profile(**d)


def test_langs_reach_profile():
    profiles = runner.load_profiles(
        r"D:\LOCAL_AI\BENCH_V5_NIGHT\config\profiles.json")
    assert profiles["nomic-embed-text:latest"].langs == ["en"]
    assert profiles["bge-m3:latest"].langs == ["multi"]


def test_oom_ram_explicit_phrases():
    # must be OOM_RAM
    for body in ("CUDA error: out of memory, system memory exhausted",
                 "failed to allocate host memory",
                 "out of memory: cpu buffer full",
                 "not enough memory for allocation",
                 "insufficient memory",
                 "out of memory in RAM area"):
        st, _, _ = runner.classify_exception(
            OllamaError("x", http_status=500, body=body))
        assert st == "OOM_RAM", body
    # bare words containing 'ram' must NOT match
    for body in ("CUDA error: out of memory in program cache",
                 "out of memory: parameter buffer"):
        st, _, _ = runner.classify_exception(
            OllamaError("x", http_status=500, body=body))
        assert st == "OOM_GPU", body
    # plain OOM stays GPU
    st, _, _ = runner.classify_exception(
        OllamaError("x", http_status=500, body="CUDA error: out of memory"))
    assert st == "OOM_GPU"


def test_truncated_empty_attribution_model():
    args = argparse.Namespace(run_id="r", budget_hours=0.1, smoke=False,
                              min_case_s=5.0)

    class FakeMod:
        META = {"version": "n1", "mode": "R0"}

        def validate(self, case, resp, profile):
            from bench.types import Verdict
            return Verdict(status="OK", sem=0.7, strict=0.7,
                           details={}, attribution="MODEL")

    class FakeCtx:
        modules = {"HOME-90": FakeMod()}
        digest_by_tag = {}
        ollama_version = "mock"
        baseline = {}
        monitor = None
        def __init__(self):
            self.args = args

    case = Case(id="HOME-90-001", test_id="HOME-90")
    p = _prof()
    meta = {"version": "n1", "mode": "R0"}
    inv = {"endpoint": "chat", "think": False}
    rec = runner.finalize_response(FakeCtx(), p, meta, case,
                                   Response(content="half", done_reason="length"),
                                   inv, [])
    assert rec["verdict"]["status"] == "OUTPUT_TRUNCATED"
    assert rec["verdict"]["sub_reason"] == "IN_ANSWER"
    assert rec["verdict"]["attribution"] == "MODEL"
    rec2 = runner.finalize_response(FakeCtx(), p, meta, case,
                                    Response(content="", thinking="",
                                             done_reason="length"), inv, [])
    assert rec2["verdict"]["sub_reason"] == "IN_THINKING"
    assert rec2["verdict"]["attribution"] == "MODEL"
    rec3 = runner.finalize_response(FakeCtx(), p, meta, case,
                                    Response(content="", thinking="t",
                                             done_reason="stop"), inv, [])
    assert rec3["verdict"]["status"] == "EMPTY_OUTPUT"
    assert rec3["verdict"]["sub_reason"] == "EMPTY_AFTER_THINKING"
    assert rec3["verdict"]["attribution"] == "MODEL"


def test_parse_offload_layers():
    assert runner.parse_offload_layers("llama: offloaded 12/33 layers") == (12, 33)
    assert runner.parse_offload_layers("no match here") == (None, None)


def test_capture_load_info_and_enrich():
    class FakeClient:
        def ps(self):
            return {"models": [{"name": "m:latest", "size": 1000,
                                "size_vram": 800, "context_length": 4096}]}

    class FakeCtx:
        client = FakeClient()
        load_info = {}
        server_log_path = os.path.join("nope", "server.log")
        server_log_offset = 0

    info = runner.capture_load_info(FakeCtx(), "m:latest")
    assert info["size"] == 1000 and info["size_vram"] == 800
    assert abs(info["offload_ratio"] - 0.8) < 1e-9
    assert info["context_length"] == 4096
    rec = {"verdict": {"details": {"phase": "cold_load"}}, "load_info": {}}
    runner.enrich_perf_record(rec, info)
    assert rec["verdict"]["details"]["offload_ratio"] == 0.8
    assert rec["load_info"]["size"] == 1000


def test_sort_by_actual_size():
    tags = ["big:latest", "small:latest", "mid:latest"]
    sizes = {"big:latest": 9_000_000_000, "small:latest": 1_000_000_000,
             "mid:latest": 4_000_000_000}
    assert runner.sort_by_actual_size(tags, sizes) == [
        "small:latest", "mid:latest", "big:latest"]
    profiles = {t: _prof(tag=t) for t in tags}
    assert runner.select_models(profiles, None, False, sizes)[0] == "small:latest"


def test_estimate_measured_and_fallback():
    import bench.store as storemod

    class FakeStore:
        def load_all(self):
            return [
                {"key": "r|OLLAMA|home-model:latest@abc12345|HOME-90@n1|HOME-90-001|0|R0|p",
                 "verdict": {"status": "OK"}, "timing": {"wall_s": 10.0}},
                {"key": "r|OLLAMA|home-model:latest@abc12345|HOME-90@n1|HOME-90-002|0|R0|p",
                 "verdict": {"status": "OK"}, "timing": {"wall_s": 12.0}},
            ]

    class FakeMod:
        META = {"id": "HOME-90", "home": "home-model:latest", "family": "TEXT",
                "kind": "chat", "mode": "R0", "core_n": 2, "timeout_s": 120,
                "num_predict": 100, "think_extra": 0, "version": "n1"}

    args = argparse.Namespace(run_id="r", budget_hours=1, smoke=False,
                              min_case_s=5.0)
    ctx = argparse.Namespace(args=args, modules={"HOME-90": FakeMod()},
                             speeds={"home-model:latest": {"gen_tok_s": 20.0},
                                     "fast-model:latest": {"gen_tok_s": 40.0}},
                             store=FakeStore())
    prof = _prof(tag="fast-model:latest")
    meta = dict(FakeMod.META)
    est = runner.estimate_block_s(ctx, prof, meta, 2)
    # median 11 * (20/40) = 5.5 per case -> 2*5.5+20
    assert abs(est - (2 * 5.5 + 20.0)) < 1e-6
    # tools_loop multiplies by 3
    meta_tools = dict(meta, kind="tools_loop")
    est2 = runner.estimate_block_s(ctx, prof, meta_tools, 1)
    assert abs(est2 - (5.5 * 3 + 20.0)) < 1e-6
    # fallback when no home data: 0.5*npred path, clipped
    ctx2 = argparse.Namespace(args=args, modules={"HOME-90": FakeMod()},
                              speeds={}, store=FakeStore())
    est3 = runner.estimate_block_s(ctx2, _prof(tag="x"), meta, 1)
    assert est3 > 0


def test_monitor_window_and_baseline(tmp_path):
    mon = envmod.Monitor(str(tmp_path / "tel.csv"), interval_s=1000)
    t0 = time.time()
    mon.add_sample({"gpu_util": 10.0, "vram_used_mb": 100.0, "temp_c": 40.0,
                    "throttle_reasons": "Not Active"}, ts=t0 + 1)
    mon.add_sample({"gpu_util": 30.0, "vram_used_mb": 200.0, "temp_c": 50.0,
                    "throttle_reasons": "0x40"}, ts=t0 + 2)
    stats = mon.window_stats(t0, t0 + 3)
    assert stats["samples"] == 2
    assert stats["vram_peak_mb"] == 200.0
    assert stats["gpu_util_mean"] == 20.0
    assert stats["temp_start"] == 40.0 and stats["temp_peak"] == 50.0
    assert stats["throttle"] is True
    # empty window
    assert mon.window_stats(t0 + 100, t0 + 200)["samples"] == 0
    # compute_resources uses baseline from ctx
    ctx = argparse.Namespace(baseline={"vram_baseline_mb": 111.0}, monitor=mon)
    res = runner.compute_resources(ctx, t0, t0 + 3)
    assert res["vram_peak_mb"] == 200.0
    assert res["vram_baseline_mb"] == 111.0


def test_report_coverage_overview_home_pairwise(tmp_path):
    from bench import report as R

    def rec(model, test, case, status, sem, wall=1.0):
        return {"key": f"r|OLLAMA|{model}@abc|{test}@n1|{case}|0|R0|p",
                "identity": {"tag": model}, "response": {},
                "timing": {"wall_s": wall},
                "resources": {}, "flags": [],
                "verdict": {"status": status, "sem": sem, "strict": sem,
                            "sub_reason": "", "attribution": "MODEL",
                            "details": {}}}

    run_dir = str(tmp_path)
    recs = []
    # home m1 scores 6/6, competitor m2 scores 3/6 + 3 timeouts (coverage 0.5)
    for i in range(6):
        recs.append(rec("m1", "HOME-16", f"HOME-16-00{i}", "OK", 1.0))
    for i in range(3):
        recs.append(rec("m2", "HOME-16", f"HOME-16-00{i}", "OK", 1.0))
    for i in range(3, 6):
        recs.append(rec("m2", "HOME-16", f"HOME-16-00{i}", "TIMEOUT", 0.0))
    recs.append(rec("m1", "PERF", "perf_cold_1", "OK", 1.0))
    with open(os.path.join(run_dir, "results.jsonl"), "w",
              encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    out = R.write_report(run_dir)
    rows = {r["model"]: r for r in out["per_test"]["HOME-16"]}
    assert rows["m2"]["insufficient_coverage"] is True
    assert rows["m1"]["insufficient_coverage"] is False
    assert out["overview"]["not_run_budget"] == 0
    assert out["overview"]["n_models"] == 2
    assert "Run overview" in open(os.path.join(run_dir, "summary.md"),
                                  encoding="utf-8").read()
    assert "insufficient coverage" in open(
        os.path.join(run_dir, "summary.md"), encoding="utf-8").read()
