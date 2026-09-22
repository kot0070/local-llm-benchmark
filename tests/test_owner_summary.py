"""Tests for tools/owner_summary.py (no network, no Ollama)."""
import csv
import json
import os
import subprocess
import sys

import pytest

TOOL = [sys.executable, os.path.join("tools", "owner_summary.py")]
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

MODELS = ["model-a:1b", "model-b:1b", "model-c:1b"]
DIGEST = "abc123"


def _rec(model, test, case, status, sem, sub=""):
    return {"key": f"r|OLLAMA|{model}@{DIGEST}|{test}@n1|{case}|0|R0|p",
            "identity": {"tag": model, "digest": DIGEST,
                         "ollama_version": "0.34.2"},
            "response": {"content": "x", "thinking": "", "tool_calls": [],
                         "tool_call_channel": "none", "done_reason": "stop",
                         "prompt_eval_count": 1, "eval_count": 1},
            "timing": {"load_s": 0.1, "ttft_s": 0.2, "prompt_eval_s": 0.1,
                       "eval_s": 0.5, "prompt_tok_s": 10.0, "gen_tok_s": 2.0,
                       "wall_s": 1.0, "first_after_load": None},
            "resources": {"vram_peak_mb": 100.0, "vram_baseline_mb": 50.0,
                          "gpu_util_mean": 5.0, "temp_start": 40.0,
                          "temp_peak": 45.0, "throttle": False},
            "verdict": {"status": status, "sub_reason": sub,
                        "attribution": "MODEL", "sem": sem, "strict": sem,
                        "details": {}},
            "flags": [],
            "timestamps": {"utc": "2026-09-21T15:00:00+00:00",
                           "local": "2026-09-21T10:00:00-05:00"}}


def _write_run(run_dir, recs, with_perf=True, with_manifest=True):
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "results.jsonl"), "w",
              encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    if with_perf:
        with open(os.path.join(run_dir, "perf.csv"), "w", newline="",
                  encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["tag", "cold_load_s", "ttft_s", "prompt_tok_s",
                        "gen_tok_s", "vram_peak_mb", "offload_ratio",
                        "throttle"])
            for m, g in (("model-a:1b", 50.0), ("model-b:1b", 20.0),
                         ("model-c:1b", 10.0)):
                w.writerow([m, 1.0, 0.2, 1000.0, g, 500.0, 1.0, False])
    if with_manifest:
        man = {"run_id": os.path.basename(run_dir),
               "start_utc": "2026-09-21T14:00:00+00:00",
               "start_local": "2026-09-21T09:00:00-05:00",
               "budget_hours": 8,
               "ollama_version": "0.34.2",
               "fingerprint": {"gpu": "TEST-GPU", "cpu": "TEST-CPU",
                               "ram": "TEST-RAM", "os": "TEST-OS"}}
        with open(os.path.join(run_dir, "manifest.json"), "w",
                  encoding="utf-8") as f:
            json.dump(man, f)


def _synthetic_recs():
    recs = []
    # HOME-01: a strong, b weak, c UNSUPPORTED-only (must stay out of top-3)
    for i in range(3):
        recs.append(_rec("model-a:1b", "HOME-01", f"HOME-01-c{i}", "OK", 1.0))
        recs.append(_rec("model-b:1b", "HOME-01", f"HOME-01-c{i}",
                         "WRONG_ANSWER", 0.0))
    for i in range(2):
        recs.append(_rec("model-c:1b", "HOME-01", f"HOME-01-c{i}",
                         "UNSUPPORTED_CAPABILITY", 0.0, sub="LANG"))
    # HOME-02: a + b scored, one NOT_RUN_BUDGET (partial-run note)
    for i in range(2):
        recs.append(_rec("model-a:1b", "HOME-02", f"HOME-02-c{i}", "OK", 1.0))
        recs.append(_rec("model-b:1b", "HOME-02", f"HOME-02-c{i}", "OK", 0.5))
    recs.append(_rec("model-b:1b", "HOME-02", "HOME-02-c9",
                     "NOT_RUN_BUDGET", 0.0, sub="BUDGET"))
    # PERF rows (also covered by perf.csv)
    for m in MODELS:
        recs.append(_rec(m, "PERF", "perf_cold_1", "OK", 1.0, sub="COLD_LOAD"))
    return recs


def _run_tool(run_dir):
    r = subprocess.run(TOOL + [run_dir], cwd=ROOT, capture_output=True,
                       text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    return os.path.join(run_dir, "OWNER_SUMMARY_UK.md")


HEADERS = ["Огляд прогону", "HOME-вердикти", "Топ-3 по кожному тесту",
           "Швидкість на цьому ПК", "Профіль моделей",
           "Відомі особливості моделей", "Обмеження"]


def test_synthetic_run(tmp_path):
    run_dir = str(tmp_path / "SYNTH")
    _write_run(run_dir, _synthetic_recs())
    md_path = _run_tool(run_dir)
    assert os.path.exists(md_path)
    assert os.path.exists(os.path.join(run_dir, "owner_tables.csv"))
    with open(md_path, encoding="utf-8") as f:
        md = f.read()
    for h in HEADERS:
        assert h in md, f"missing section header: {h}"
    # UNSUPPORTED-only model-c must not appear as a ranked top-3 row
    sec3 = md.split("Топ-3 по кожному тесту")[1].split("Швидкість")[0]
    assert "model-c:1b: Q_sem" not in sec3
    # partial-run note
    assert "частковий прогін:" in md
    assert "NOT_RUN_BUDGET" in md


def test_empty_results_no_crash(tmp_path):
    run_dir = str(tmp_path / "EMPTY")
    _write_run(run_dir, [], with_perf=False, with_manifest=False)
    md_path = _run_tool(run_dir)
    assert os.path.exists(md_path)
    with open(md_path, encoding="utf-8") as f:
        md = f.read()
    for h in HEADERS:
        assert h in md


def _rec_details(model, test, case, status, sem, sub=None,
                   details_sub=None):
    r = _rec(model, test, case, status, sem, sub=sub or "")
    if details_sub is not None:
        r["verdict"]["sub_reason"] = sub
        r["verdict"]["details"] = {"sub_reason": details_sub}
    return r


def test_notrun_only_model_not_scored(tmp_path):
    sys.path.insert(0, ROOT)
    from tools import owner_summary as osum
    from bench import report as rep
    run_dir = str(tmp_path / "NOTRUN")
    recs = [
        _rec("model-a:1b", "HOME-01", "HOME-01-c0", "OK", 1.0),
        _rec("model-a:1b", "HOME-01", "HOME-01-c1", "OK", 0.0),
        _rec("model-b:1b", "HOME-01", "HOME-01-c0", "NOT_RUN_BUDGET",
             0.0, sub="BUDGET"),
        _rec("model-b:1b", "HOME-01", "HOME-01-c1", "NOT_RUN_BUDGET",
             0.0, sub="BUDGET"),
    ]
    _write_run(run_dir, recs, with_perf=False, with_manifest=True)
    records = rep.load_records(run_dir)
    per_test, per_model, _ = rep.compute_tables(records)
    row_b = next(r for r in per_test["HOME-01"]
                 if r["model"] == "model-b:1b")
    assert row_b["n_scored"] == 0
    assert osum._unscored_label(row_b) == "не оцінено (NOT_RUN_BUDGET)"
    assert osum._q_cell(row_b) == "не оцінено (NOT_RUN_BUDGET)"
    # unsup label
    row_u = {"n_scored": 0, "counts": {"UNSUPPORTED_CAPABILITY": 2}}
    assert osum._unscored_label(row_u) == "не оцінено (UNSUPPORTED)"
    # per-model mean excludes unscored: model-b has no scored test
    lines = osum._profile_lines(per_model, records, {})
    line_b = next(ln for ln in lines if ln.startswith("- model-b:1b:"))
    assert "середній Q_sem=не оцінено" in line_b
    assert "Q_sem=0.000" not in line_b
    line_a = next(ln for ln in lines if ln.startswith("- model-a:1b:"))
    assert "середній Q_sem=0.500" in line_a
    # mixed model: one scored + one NOT_RUN-only -> mean uses scored only
    recs2 = recs + [_rec("model-a:1b", "HOME-02", "HOME-02-c0",
                         "NOT_RUN_BUDGET", 0.0, sub="BUDGET")]
    _write_run(str(tmp_path / "MIX"), recs2, with_perf=False,
               with_manifest=True)
    records2 = rep.load_records(str(tmp_path / "MIX"))
    _, per_model2, _ = rep.compute_tables(records2)
    lines2 = osum._profile_lines(per_model2, records2, {})
    line_a2 = next(ln for ln in lines2 if ln.startswith("- model-a:1b:"))
    assert "середній Q_sem=0.500" in line_a2
    # CSV: empty cells + note
    osum.write_tables_csv(run_dir, records)
    with open(os.path.join(run_dir, "owner_tables.csv"), encoding="utf-8",
              newline="") as f:
        rows = list(csv.DictReader(f))
    rb = next(r for r in rows if r["model"] == "model-b:1b")
    assert rb["q_sem"] == "" and rb["q_strict"] == ""
    assert rb["ci_lo"] == "" and rb["ci_hi"] == ""
    assert rb["note"] == "NOT_RUN_BUDGET"
    ra = next(r for r in rows if r["model"] == "model-a:1b")
    assert ra["q_sem"] != "" and ra["note"] == ""


def test_details_sub_reason_used(tmp_path):
    sys.path.insert(0, ROOT)
    from tools import owner_summary as osum
    from bench import report as rep
    run_dir = str(tmp_path / "SUBR")
    recs = [
        _rec_details("model-a:1b", "HOME-01", "HOME-01-c0", "FORMAT_ERROR",
                     0.5, sub=None, details_sub="CONTRACT_BROKEN"),
        _rec_details("model-a:1b", "HOME-01", "HOME-01-c1", "FORMAT_ERROR",
                     0.5, sub=None, details_sub="CONTRACT_BROKEN"),
    ]
    _write_run(run_dir, recs, with_perf=False, with_manifest=True)
    records = rep.load_records(run_dir)
    _, per_model, _ = rep.compute_tables(records)
    lines = osum._profile_lines(per_model, records, {})
    line = next(ln for ln in lines if "model-a:1b" in ln)
    assert "FORMAT_ERROR[CONTRACT_BROKEN]" in line
    assert "FORMAT_ERROR[-]" not in line


def test_cpu_fallback_mocked(monkeypatch):
    sys.path.insert(0, ROOT)
    from tools import owner_summary as osum
    osum._LOCAL_MACHINE_CACHE = None
    monkeypatch.setattr(osum, "_query_local_machine",
                        lambda: ("TEST-CPU-X", "32.0 GB"))
    cpu, ram = osum._cpu_ram_text({"cpu": "unknown", "ram": "unknown"})
    assert cpu == "TEST-CPU-X (зчитано з поточної системи)"
    assert ram == "32.0 GB (зчитано з поточної системи)"
    # known values are not replaced and do not query
    osum._LOCAL_MACHINE_CACHE = None
    def _boom():
        raise AssertionError("must not query when values known")
    monkeypatch.setattr(osum, "_query_local_machine", _boom)
    cpu2, ram2 = osum._cpu_ram_text({"cpu": "RealCPU", "ram": "RealRAM"})
    assert (cpu2, ram2) == ("RealCPU", "RealRAM")


def test_cpu_fallback_failure_path(monkeypatch):
    sys.path.insert(0, ROOT)
    from tools import owner_summary as osum
    osum._LOCAL_MACHINE_CACHE = None
    monkeypatch.setattr(osum, "_query_local_machine",
                        lambda: (None, None))
    cpu, ram = osum._cpu_ram_text({"cpu": "", "ram": "unknown"})
    assert cpu == osum.NO_DATA and ram == osum.NO_DATA


def test_language_note_above_english_bullets(tmp_path):
    sys.path.insert(0, ROOT)
    from tools import owner_summary as osum
    run_dir = str(tmp_path / "LANG")
    _write_run(run_dir, _synthetic_recs())
    records = __import__("bench.report", fromlist=["x"]).load_records(run_dir)
    manifest = osum._load_manifest(run_dir)
    import csv as _csv
    with open(os.path.join(run_dir, "perf.csv"), encoding="utf-8",
              newline="") as f:
        perf = list(_csv.DictReader(f))
    md = osum.build_markdown("LANG", manifest, records, perf)
    sec6 = md.split("Відомі особливості моделей")[1].split("## 7.")[0]
    note_pos = sec6.find("англійською мовою")
    assert note_pos != -1
    first_bullet = sec6.find("- ")
    assert first_bullet != -1 and note_pos < first_bullet


def test_gv_pointer_present_and_absent(tmp_path):
    sys.path.insert(0, ROOT)
    from tools import owner_summary as osum
    from bench import report as rep
    run_dir = str(tmp_path / "GVMAIN")
    _write_run(run_dir, _synthetic_recs())
    records = rep.load_records(run_dir)
    manifest = osum._load_manifest(run_dir)
    perf = osum._load_perf(run_dir)
    md_no_gv = osum.build_markdown("GVMAIN", manifest, records, perf,
                                   gv_exists=False)
    assert "додатковий прогін" not in md_no_gv
    md_gv = osum.build_markdown("GVMAIN", manifest, records, perf,
                                gv_exists=True)
    assert "GVMAIN_gv" in md_gv
    assert "не порівнюється напряму" in md_gv
    assert "ANALYSIS_UK.md" in md_gv
    # pointer sits directly under the HOME-verdicts table (section 2)
    sec2 = md_gv.split("HOME-вердикти")[1].split("## 3.")[0]
    assert "додатковий прогін" in sec2


def test_profile_test_count_qualifier(tmp_path):
    sys.path.insert(0, ROOT)
    from tools import owner_summary as osum
    from bench import report as rep
    run_dir = str(tmp_path / "QUAL")
    _write_run(run_dir, _synthetic_recs())
    records = rep.load_records(run_dir)
    _, per_model, _ = rep.compute_tables(records)
    lines = osum._profile_lines(per_model, records, {})
    assert lines
    for ln in lines:
        assert "тестів:" in ln and "(без PERF)" in ln
    assert not any("тестів: 2;" in ln or "тестів: 1;" in ln for ln in lines)


SMOKE_RUNS = ["SMOKE2b", "SMOKE3", "SMOKE4"]


@pytest.mark.parametrize("run_id", SMOKE_RUNS)
def test_smoke_runs_exit_0(run_id):
    run_dir = os.path.join(ROOT, "results", run_id)
    if not os.path.isdir(run_dir):
        pytest.skip(f"missing {run_dir}")
    before = set(os.listdir(run_dir))
    r = subprocess.run(TOOL + [run_id], cwd=ROOT, capture_output=True,
                       text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    md_path = os.path.join(run_dir, "OWNER_SUMMARY_UK.md")
    assert os.path.exists(md_path)
    with open(md_path, encoding="utf-8") as f:
        md = f.read()
    for h in HEADERS:
        assert h in md
    # tool writes only its own output files
    new_files = set(os.listdir(run_dir)) - before
    assert new_files <= {"OWNER_SUMMARY_UK.md", "owner_tables.csv",
                         "owner_summary.xlsx"}, new_files
