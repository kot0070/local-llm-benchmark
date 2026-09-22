"""Tests for tools/build_excel_report.py (no network, no Ollama)."""
import csv
import json
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.build_excel_report import SHEET_NAMES, main  # noqa: E402

DIGEST = "abc123"


def _rec(model, test, case, status, sem, sub=""):
    return {"key": "r|OLLAMA|%s@%s|%s@n1|%s|0|R0|p" % (model, DIGEST, test, case),
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
            w.writerow(["clean-ok:1b", 1.0, 0.2, 1000.0, 50.0, 500.0, 1.0,
                        False])
            w.writerow(["fail-model:7b", 9.0, 0.5, 800.0, 5.0, 7000, 0.5,
                        False])
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
    for i in range(3):  # clean model, all OK
        recs.append(_rec("clean-ok:1b", "HOME-01", "HOME-01-c%d" % i,
                         "OK", 1.0))
    # failing model: 2 OK + 2 WRONG -> Q_sem 0.5 on HOME-03
    for i in range(2):
        recs.append(_rec("fail-model:7b", "HOME-03", "HOME-03-c%d" % i,
                         "OK", 1.0))
    for i in range(2, 4):
        recs.append(_rec("fail-model:7b", "HOME-03", "HOME-03-c%d" % i,
                         "WRONG_ANSWER", 0.0, sub="EVIDENCE_MISMATCH"))
    # UNSUPPORTED-only model (must show "поза рейтингом", no fabricated Q)
    for i in range(2):
        recs.append(_rec("unsup-model:1b", "HOME-02", "HOME-02-c%d" % i,
                         "UNSUPPORTED_CAPABILITY", 0.0, sub="LANG"))
    # NOT_RUN_BUDGET-only pair
    for i in range(2):
        recs.append(_rec("clean-ok:1b", "HOME-04", "HOME-04-c%d" % i,
                         "NOT_RUN_BUDGET", 0.0, sub="BUDGET"))
    return recs


def _open_xlsx(path):
    import openpyxl
    return openpyxl.load_workbook(path, data_only=True)


def test_synthetic_sheets_values_and_determinism(tmp_path):
    from bench import report as rep
    run_dir = str(tmp_path / "SYNTH")
    _write_run(run_dir, _synthetic_recs())
    assert main([run_dir]) == 0
    out = os.path.join(run_dir, "NIGHT1_REPORT.xlsx")
    assert os.path.exists(out)
    with open(out, "rb") as f:
        first_bytes = f.read()
    assert main([run_dir]) == 0  # rerun: byte-identical output
    with open(out, "rb") as f:
        assert f.read() == first_bytes
    wb = _open_xlsx(out)
    assert wb.sheetnames == SHEET_NAMES
    # header row present and bold on every sheet
    for ws in wb.worksheets:
        assert ws.max_row >= 1 and ws.max_column >= 1
        assert ws["A1"].value not in (None, "")
        assert ws["A1"].font.bold is True
        assert ws.freeze_panes == "A2"
    # rating: fail-model HOME-03 Q_sem matches bench.report independently
    records = rep.load_records(run_dir)
    per_test, _, _ = rep.compute_tables(records)
    exp = next(r for r in per_test["HOME-03"]
               if r["model"] == "fail-model:7b")
    ws = wb["Рейтинг по тестах"]
    found = None
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] == "HOME-03" and row[1] == "fail-model:7b":
            found = row
            break
    assert found is not None
    assert found[2] == pytest.approx(exp["q_sem"], abs=1e-9)
    # UNSUPPORTED-only row labelled, not ranked with a fabricated score
    ws_rows = list(ws.iter_rows(min_row=2, values_only=True))
    unsup = [r for r in ws_rows
             if r[0] == "HOME-02" and r[1] == "unsup-model:1b"]
    assert len(unsup) == 1
    assert unsup[0][-1] == "поза рейтингом"
    # NOT_RUN_BUDGET-only row labelled as well
    notrun = [r for r in ws_rows
              if r[0] == "HOME-04" and r[1] == "clean-ok:1b"]
    assert len(notrun) == 1
    assert notrun[0][-1] == "поза рейтингом"
    # verdicts sheet: one row per HOME test (24) + header
    wv = wb["HOME-вердикти"]
    assert wv.max_row == 25
    # HOME-07 sheet exists with the non-comparability note
    w7 = wb["HOME-07 (окремий прогін)"]
    texts = " ".join(str(c.value or "") for row in w7.iter_rows()
                     for c in row)
    assert "не порівнюються" in texts


def test_missing_gen_tok_s_writes_no_data(tmp_path):
    run_dir = str(tmp_path / "NODATA")
    recs = [_rec("embed-only:1b", "HOME-02", "HOME-02-c0",
                  "UNSUPPORTED_CAPABILITY", 0.0, sub="LANG")]
    for i in range(2):
        recs.append(_rec("text-model:1b", "HOME-01", "HOME-01-c%d" % i,
                          "OK", 1.0))
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "results.jsonl"), "w",
              encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(run_dir, "perf.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tag", "cold_load_s", "ttft_s", "prompt_tok_s",
                    "gen_tok_s", "vram_peak_mb", "offload_ratio",
                    "throttle"])
        w.writerow(["embed-only:1b", 1.0, 0.2, 1000.0, "", 500.0, 1.0,
                    False])
        w.writerow(["text-model:1b", 1.0, 0.2, 1000.0, 50.0, 500.0, 1.0,
                    False])
    man = {"run_id": "NODATA",
           "start_local": "2026-09-21T09:00:00-05:00",
           "budget_hours": 8}
    with open(os.path.join(run_dir, "manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(man, f)
    assert main([run_dir]) == 0
    wb = _open_xlsx(os.path.join(run_dir, "NIGHT1_REPORT.xlsx"))
    prof = wb["Профілі моделей"]
    gen_col = next(c.column for c in prof[1]
                   if c.value == "gen tok/s")
    emb_row = next(r for r in prof.iter_rows(min_row=2, values_only=True)
                   if r[0] == "embed-only:1b")
    assert emb_row[gen_col - 1] == "немає даних"
    txt_row = next(r for r in prof.iter_rows(min_row=2, values_only=True)
                   if r[0] == "text-model:1b")
    assert txt_row[gen_col - 1] == 50.0
    spd = wb["Швидкість"]
    spd_gen = next(c.column for c in spd[1]
                   if str(c.value or "") == "gen tok/s")
    emb_spd = next(r for r in spd.iter_rows(min_row=2, values_only=True)
                   if r[0] == "embed-only:1b")
    assert emb_spd[spd_gen - 1] == "немає даних"


def test_empty_results_no_crash(tmp_path):
    run_dir = str(tmp_path / "EMPTY")
    _write_run(run_dir, [], with_perf=False, with_manifest=False)
    assert main([run_dir]) == 0
    out = os.path.join(run_dir, "NIGHT1_REPORT.xlsx")
    assert os.path.exists(out)
    wb = _open_xlsx(out)
    assert wb.sheetnames == SHEET_NAMES


def test_strengths_sheet_synthetic_traceable(tmp_path):
    from tools.build_excel_report import STRONG_HEADER, STRONG_NONE, WEAK_NONE
    run_dir = str(tmp_path / "SYNTH2")
    _write_run(run_dir, _synthetic_recs())
    assert main([run_dir]) == 0
    out = os.path.join(run_dir, "NIGHT1_REPORT.xlsx")
    wb = _open_xlsx(out)
    # name + position: after "Профілі моделей", before "Швидкість"
    assert wb.sheetnames[4] == "Сильні та слабкі сторони"
    assert wb.sheetnames.index("Профілі моделей") + 1 == \
        wb.sheetnames.index("Сильні та слабкі сторони")
    assert wb.sheetnames.index("Сильні та слабкі сторони") + 1 == \
        wb.sheetnames.index("Швидкість")
    ws = wb["Сильні та слабкі сторони"]
    assert [c.value for c in ws[1]] == STRONG_HEADER
    assert ws["A1"].font.bold is True
    assert ws.freeze_panes == "A2"
    rows = {r[0]: r for r in ws.iter_rows(min_row=2, values_only=True)
            if r[0]}
    assert sorted(rows) == sorted(["clean-ok:1b", "fail-model:7b",
                                   "unsup-model:1b"])
    # clean model: real strength cites its own data; weakness is honest
    assert "HOME-01" in rows["clean-ok:1b"][1]
    assert "1.000" in rows["clean-ok:1b"][1]
    assert rows["clean-ok:1b"][2] == WEAK_NONE
    # failing model: honest no-strength; weakness cites injected sub_reason
    assert rows["fail-model:7b"][1] == STRONG_NONE
    assert "EVIDENCE_MISMATCH" in rows["fail-model:7b"][2]
    assert "0.500" in rows["fail-model:7b"][2]
    # unsupported-only model: no scored evidence either way -> honest both
    assert rows["unsup-model:1b"][1] == STRONG_NONE
    assert rows["unsup-model:1b"][2] == WEAK_NONE
    # recommendation always names hardware numbers or their absence;
    # source always points back to evidence
    assert "холод" in rows["clean-ok:1b"][3].lower() or \
        "cold load" in rows["clean-ok:1b"][3]
    assert "perf.csv" in rows["clean-ok:1b"][4]
    assert "fail-model:7b" in rows["fail-model:7b"][4]
    # wrap text + taller rows (long cells must not truncate)
    for row in ws.iter_rows(min_row=2, max_col=5):
        for cell in row[1:4]:
            assert cell.alignment.wrap_text is True
        assert ws.row_dimensions[row[0].row].height >= 40


REAL_RUN = os.path.join(ROOT, "results", "night_20260921-155146")


def test_real_run_exit_0_and_readonly():
    if not os.path.isdir(REAL_RUN):
        pytest.skip("missing real run dir")
    before = set(os.listdir(REAL_RUN))
    assert main(["night_20260921-155146"]) == 0
    out = os.path.join(REAL_RUN, "NIGHT1_REPORT.xlsx")
    assert os.path.exists(out)
    wb = _open_xlsx(out)
    assert wb.sheetnames == SHEET_NAMES
    # tool writes only its own declared output file
    new_files = set(os.listdir(REAL_RUN)) - before
    assert new_files <= {"NIGHT1_REPORT.xlsx"}, new_files
