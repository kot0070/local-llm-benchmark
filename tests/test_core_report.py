"""Report + eligibility + gen_all tests (no network)."""
import json
import os
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def _rec(model, test, case, status, sem, strict=None, wall=1.0):
    return {"key": f"r|OLLAMA|{model}@abc|{test}@n1|{case}|0|R0|p",
            "identity": {"tag": model, "digest": "abc",
                         "ollama_version": "mock"},
            "response": {"content": "", "thinking": "", "tool_calls": [],
                         "tool_call_channel": "none", "done_reason": "stop",
                         "prompt_eval_count": 1, "eval_count": 1},
            "timing": {"load_s": 0.1, "ttft_s": 0.2, "prompt_eval_s": 0.1,
                       "eval_s": 0.5, "prompt_tok_s": 10.0, "gen_tok_s": 2.0,
                       "wall_s": wall, "first_after_load": None},
            "resources": {"vram_peak_mb": 100.0, "vram_baseline_mb": 50.0,
                          "gpu_util_mean": 5.0, "temp_start": 40.0,
                          "temp_peak": 45.0, "throttle": False},
            "verdict": {"status": status, "sub_reason": "", "attribution": "MODEL",
                        "sem": sem,
                        "strict": sem if strict is None else strict,
                        "details": {}},
            "flags": []}


def test_report_tables_and_csvs(tmp_path):
    from bench import report as reportmod
    run_dir = str(tmp_path)
    recs = []
    for i in range(6):
        recs.append(_rec("m1", "HOME-16", f"HOME-16-00{i}", "OK", 1.0))
        recs.append(_rec("m2", "HOME-16", f"HOME-16-00{i}",
                         "OK" if i < 3 else "WRONG_ANSWER",
                         1.0 if i < 3 else 0.0))
    recs.append(_rec("m1", "HOME-16", "HOME-16-99", "TIMEOUT", 0.0))
    with open(os.path.join(run_dir, "results.jsonl"), "w",
              encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    out = reportmod.write_report(run_dir)
    assert out["n_records"] == len(recs)
    rows = out["per_test"]["HOME-16"]
    assert rows[0]["model"] == "m1" and rows[0]["q_sem"] == 1.0
    assert rows[1]["model"] == "m2" and rows[1]["q_sem"] == 0.5
    assert rows[0]["n_scored"] == 6  # TIMEOUT excluded from denominator
    for fn in ("results.csv", "perf.csv", "errors.csv", "summary.md"):
        assert os.path.exists(os.path.join(run_dir, fn))
    assert os.path.exists(os.path.join(run_dir, "models", "m1.md"))
    assert os.path.exists(os.path.join(run_dir, "models", "m1.json"))
    hv = out["home_verdicts"]["HOME-16"]
    assert hv["verdict"] == "HOME_WIN" and hv["best"] == "m1"


def test_bootstrap_ci_deterministic():
    from bench.report import bootstrap_ci
    assert bootstrap_ci([1.0, 1.0, 1.0]) == (1.0, 1.0)
    lo1, hi1 = bootstrap_ci([1, 1, 1, 1, 0, 0, 0, 0])
    lo2, hi2 = bootstrap_ci([1, 1, 1, 1, 0, 0, 0, 0])
    assert (lo1, hi1) == (lo2, hi2)
    assert lo1 <= 0.5 <= hi1


def test_eligibility_file_structure():
    # NIGHT-1 run file: historic artifact, its counts stay rigid.
    path = _REPO / "config" / "eligibility_night.json"
    assert path.is_file()
    with open(path, encoding="utf-8") as f:
        elig = json.load(f)
    # The run's own model set comes from the file itself (HOME-01),
    # not from profiles.json (which now also holds NIGHT-2 imports).
    run_models = set(elig["HOME-01"])
    assert len(run_models) == 24
    for i in range(1, 25):
        tid = f"HOME-{i:02d}"
        assert tid in elig, f"missing {tid}"
        assert set(elig[tid]) == run_models, f"{tid} model set drifted"
        assert len(elig[tid]) == 24, f"{tid} has {len(elig[tid])} models"
        for tag, info in elig[tid].items():
            assert info["code"] in ("E", "O", "U", "S")
            assert isinstance(info["reason"], str)
    assert len(elig["_deferred"]) == 12
    # NIGHT-2 run file: 24 tests, exactly its own 4 models.
    path2 = _REPO / "config" / "eligibility_night2.json"
    assert path2.is_file()
    with open(path2, encoding="utf-8") as f:
        elig2 = json.load(f)
    run_models2 = set(elig2["HOME-01"])
    assert len(run_models2) == 4
    for i in range(1, 25):
        tid = f"HOME-{i:02d}"
        assert tid in elig2, f"missing {tid} in night2"
        assert set(elig2[tid]) == run_models2, f"{tid} model set drifted"
        assert len(elig2[tid]) == 4, f"{tid} has {len(elig2[tid])} models"
        for tag, info in elig2[tid].items():
            assert info["code"] in ("E", "O", "U", "S")
            assert isinstance(info["reason"], str)
    # No home-model check for the NIGHT-2 file by design: all four models
    # are guests (runner shows home=None), so no test has a home model
    # that must be eligible on its own test.
    # Inclusion invariant (replaces the old equality): every model named in
    # either run file must exist in profiles.json. The reverse is not
    # required -- a profile may exist without taking part in a given run
    # (this is what broke the old `== tags` check when NIGHT-2 added 4).
    with open(_REPO / "config" / "profiles.json",
              encoding="utf-8") as f:
        tags = set(json.load(f)["profiles"])
    for label, mapping in (("night", elig), ("night2", elig2)):
        mentioned = set()
        for tid, entry in mapping.items():
            if tid.startswith("_"):
                continue
            mentioned |= set(entry)
        missing = mentioned - tags
        assert not missing, f"{label} mentions unknown profiles: {missing}"
    # home model of each NIGHT-1 test is eligible on its own test
    home_of = {"HOME-01": "aya-expanse:8b", "HOME-02": "bge-m3:latest",
               "HOME-20": "sqlcoder:7b", "HOME-24": "functiongemma:270m",
               "HOME-11": "nomic-embed-text:latest"}
    for tid, tag in home_of.items():
        assert elig[tid][tag]["code"] == "E", f"{tag} not E on {tid}"


def test_gen_all_empty_and_missing_only(tmp_path, capsys):
    from tools import gen_all
    empty = tmp_path / "gen"
    empty.mkdir()
    assert gen_all.main(["--gen-dir", str(empty)]) == 0
    # generator that writes a marker
    (tmp_path / "gen_home_99.py").write_text(
        "def main():\n"
        "    open(r'" + str(tmp_path / "ran.txt") + "', 'w').write('x')\n",
        encoding="utf-8")
    assert gen_all.main(["--gen-dir", str(tmp_path), "--fixtures-root",
                         str(tmp_path)]) == 0
    assert (tmp_path / "ran.txt").exists()
