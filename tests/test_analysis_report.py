"""Tests for tools/analysis_report.py (TOOL_ANALYSIS). Stdlib + pytest only."""
import json
import os
import shutil
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.analysis_report import (INSUFFICIENT, _plural_raz, _plural_ua,
                                     _plural_zapys, _plan_notes_for_test,
                                     main)  # noqa: E402

REAL_SMOKE3 = os.path.join(ROOT, "results", "SMOKE3")


def _rec(run, tag, test, case, status, sub=None, sem=0.0, strict=0.0,
         content="", details=None):
    return {
        "key": f"{run}|OLLAMA|{tag}@abc123|{test}@n|{case}|0|R0|prof.v1",
        "identity": {"tag": tag},
        "response": {"content": content, "thinking": "", "tool_calls": [],
                     "tool_call_channel": "none", "done_reason": "stop"},
        "timing": {"wall_s": 1.0},
        "verdict": {"status": status, "sub_reason": sub,
                    "attribution": "MODEL", "sem": sem, "strict": strict,
                    "details": details or {}},
        "timestamps": {"utc": "2026-09-21T20:00:00+00:00",
                       "local": "2026-09-21T15:00:00-05:00"},
    }


def _synthetic_run(tmpdir, run_id="SYN"):
    run_dir = os.path.join(str(tmpdir), run_id)
    os.makedirs(run_dir)
    recs = []
    for i in range(6):  # clean OK model
        recs.append(_rec(run_id, "clean-ok:1b", "HOME-01",
                         f"HOME-01-{i + 1:02d}", "OK", None, 1.0, 1.0,
                         '{"answer": "ok"}'))
    quote = "SYNTHETIC_FAILURE_QUOTE_ALPHA_12345"  # < 200 chars, verbatim
    for i in range(4):  # failing model: 4 OK ...
        recs.append(_rec(run_id, "fail-model:7b", "HOME-03",
                         f"HOME-03-{i + 1:02d}", "OK", None, 1.0, 1.0,
                         '{"evidence": ["s1"]}'))
    for i in range(2):  # ... + 2 real failures to quote
        recs.append(_rec(run_id, "fail-model:7b", "HOME-03",
                         f"HOME-03-{i + 5:02d}", "WRONG_ANSWER",
                         "EVIDENCE_MISMATCH", 0.0, 0.0, quote))
    for i in range(2):  # too-few-records model
        recs.append(_rec(run_id, "few-model:1b", "HOME-16",
                         f"HOME-16-{i + 1:02d}", "OK", None, 1.0, 1.0,
                         '{"route": "A"}'))
    for i in range(3):  # UNSUPPORTED-only model (never in denominators)
        recs.append(_rec(run_id, "unsup-model:1b", "HOME-02",
                         f"HOME-02-{i + 1:02d}", "UNSUPPORTED_CAPABILITY",
                         "LANGUAGE_NOT_DOCUMENTED", 0.0, 0.0, ""))
    for i in range(2):  # NOT_RUN_BUDGET cases
        recs.append(_rec(run_id, "clean-ok:1b", "HOME-04",
                         f"HOME-04-{i + 1:02d}", "NOT_RUN_BUDGET",
                         "BLOCK_ESTIMATE_EXCEEDS_DEADLINE", 0.0, 0.0, ""))
    with open(os.path.join(run_dir, "results.jsonl"), "w",
              encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(run_dir, "manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump({"run_id": run_id,
                   "start_local": "2026-09-21T15:00:00-05:00",
                   "budget_hours": 1.0}, f, ensure_ascii=False)
    with open(os.path.join(run_dir, "perf.csv"), "w", encoding="utf-8") as f:
        f.write("tag,cold_load_s,ttft_s,prompt_tok_s,gen_tok_s,"
                "vram_peak_mb,offload_ratio,throttle\n")
        f.write("clean-ok:1b,1.0,0.1,1000.0,50.0,1000,1.0,\n")
        f.write("fail-model:7b,9.0,0.5,800.0,5.0,7000,0.5,\n")
    return run_dir, quote


def _read_md(run_dir):
    with open(os.path.join(run_dir, "ANALYSIS_UK.md"),
              encoding="utf-8") as f:
        return f.read()


def _section(md, header):
    start = md.index(header)
    nxt = md.find("\n### ", start + len(header))
    nxt2 = md.find("\n## ", start + len(header))
    cuts = [c for c in (nxt, nxt2) if c != -1]
    return md[start:min(cuts)] if cuts else md[start:]


def test_synthetic_sections_and_quote(tmp_path):
    run_dir, quote = _synthetic_run(tmp_path)
    assert main([os.path.basename(run_dir),
                 "--results-root", os.path.dirname(run_dir)]) == 0
    md = _read_md(run_dir)
    for h in ("# АНАЛІЗ ПРОГОНУ", "## 1. Огляд прогону", "## 2. Моделі",
              "## 3. Тести", "## 4. Швидкість на цьому ПК",
              "### clean-ok:1b", "### fail-model:7b", "### few-model:1b",
              "### unsup-model:1b", "### HOME-01", "### HOME-03"):
        assert h in md, h
    assert quote in md  # quoted example is a verbatim substring
    # too-few-records model gets the explicit wording, not a recommendation
    few = _section(md, "### few-model:1b")
    assert INSUFFICIENT in few
    assert "лише 2 оцінених записів" in few
    # UNSUPPORTED-only model: no scored records, excluded from denominators
    unsup = _section(md, "### unsup-model:1b")
    assert "Оцінених записів немає" in unsup
    assert INSUFFICIENT in unsup
    # clean model has no failures -> no error-examples block
    clean = _section(md, "### clean-ok:1b")
    assert "Приклади помилок" not in clean
    # NOT_RUN_BUDGET coverage note with exact count and pair
    assert "NOT_RUN_BUDGET записів: 2" in md
    assert "clean-ok:1b x HOME-04 (2)" in md
    # partial-offload sentence names the 0.5-ratio model
    assert "fail-model:7b" in md and "offload" in md


def test_deterministic_and_empty(tmp_path):
    run_dir, _ = _synthetic_run(tmp_path)
    args = [os.path.basename(run_dir), "--results-root",
            os.path.dirname(run_dir)]
    assert main(args) == 0
    with open(os.path.join(run_dir, "ANALYSIS_UK.md"),
              encoding="utf-8") as f:
        first = f.read()
    assert main(args) == 0
    assert _read_md(run_dir) == first  # byte-identical on rerun
    empty_dir = os.path.join(str(tmp_path), "EMPTY")
    os.makedirs(empty_dir)
    open(os.path.join(empty_dir, "results.jsonl"), "w").close()
    with open(os.path.join(empty_dir, "manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump({"run_id": "EMPTY"}, f)
    assert main(["EMPTY", "--results-root", str(tmp_path)]) == 0
    assert os.path.exists(os.path.join(empty_dir, "ANALYSIS_UK.md"))


def test_real_smoke3_exit_zero_readonly(tmp_path):
    if not os.path.isdir(REAL_SMOKE3):
        raise AssertionError("results/SMOKE3 missing")
    before = set(os.listdir(REAL_SMOKE3))
    work = os.path.join(str(tmp_path), "SMOKE3")
    shutil.copytree(REAL_SMOKE3, work)
    assert main(["SMOKE3", "--results-root", str(tmp_path)]) == 0
    md = _read_md(work)
    assert "## 2. Моделі" in md and "## 3. Тести" in md
    # the real tree was not touched: the tool ran on a copy
    assert set(os.listdir(REAL_SMOKE3)) == before
    assert "ANALYSIS_UK.md" not in before


def test_plan_notes_join_wrapped_bullet(tmp_path):
    plan = os.path.join(str(tmp_path), "MASTER_PLAN.md")
    with open(plan, "w", encoding="utf-8") as f:
        f.write("## 4. Fix log\n")
        f.write("- HOME-09/10: contracts `[section ids]` produced unquoted ids\n")
        f.write("  enumerated (`in_transit`, `on_hold` ...) and `_`/`-`/space\n")
        f.write("  normalised to finish the sentence.\n")
        f.write("- HOME-18: single-line bullet stays as is.\n")
        f.write("\n")
        f.write("## 5. Known model behaviours\n")
        f.write("- unrelated line without test id\n")
        f.write("  continuation that must not leak into the previous bullet.\n")
        f.write("\n")
        f.write("## 6. Rules for agents\n")
    notes = _plan_notes_for_test("HOME-09", plan_path=plan)
    assert len(notes) == 1
    full = notes[0]
    assert "normalised to finish the sentence." in full
    assert "enumerated" in full
    assert "mid-sentence cut" not in full
    # no mid-sentence cut: the joined text ends at the real sentence boundary
    assert full.rstrip().endswith("normalised to finish the sentence.")
    # single-line bullet still works unchanged
    single = _plan_notes_for_test("HOME-18", plan_path=plan)
    assert single == ["- HOME-18: single-line bullet stays as is."]
    # non-matching id returns nothing
    assert _plan_notes_for_test("HOME-99", plan_path=plan) == []


@pytest.mark.parametrize("n,expected", [
    (1, "раз"), (2, "рази"), (4, "рази"), (5, "разів"), (11, "разів"),
    (12, "разів"), (14, "разів"), (21, "раз"), (24, "рази"), (25, "разів"),
    (91, "раз"), (100, "разів"), (101, "раз"),
])
def test_plural_raz(n, expected):
    assert _plural_raz(n) == expected


@pytest.mark.parametrize("n,expected", [
    (1, "запис"), (2, "записи"), (4, "записи"), (5, "записів"),
    (11, "записів"), (12, "записів"), (14, "записів"), (21, "запис"),
    (24, "записи"), (25, "записів"), (94, "записи"), (23, "записи"),
    (100, "записів"), (101, "запис"),
])
def test_plural_zapys(n, expected):
    assert _plural_zapys(n) == expected


def test_failure_line_uses_plural_raz(tmp_path):
    run_dir, _ = _synthetic_run(tmp_path)
    assert main([os.path.basename(run_dir), "--results-root",
                 os.path.dirname(run_dir)]) == 0
    md = _read_md(run_dir)
    # 2 failures on the failing model -> "2 рази", never bare "2 раз."
    assert "— 2 рази." in md
    assert "— 2 раз." not in md.replace("— 2 рази.", "")


def test_desc_line_uses_plural_zapys(tmp_path):
    run_dir, _ = _synthetic_run(tmp_path)
    assert main([os.path.basename(run_dir), "--results-root",
                 os.path.dirname(run_dir)]) == 0
    md = _read_md(run_dir)
    # clean-ok:1b has 6 scored records -> "Оцінено 6 записів"
    assert "Оцінено 6 записів" in md
    # no line may use the wrong agreement for these known counts
    assert "Оцінено 6 запис," not in md
    # few-model:1b has 2 scored records -> "Оцінено 2 записи"
    assert "Оцінено 2 записи" in md
    assert _plural_ua(6, "запис", "записи", "записів") == "записів"


def test_single_scored_model_phrasing(tmp_path):
    run_dir, _ = _synthetic_run(tmp_path)
    assert main([os.path.basename(run_dir), "--results-root",
                 os.path.dirname(run_dir)]) == 0
    md = _read_md(run_dir)
    # HOME-01 is scored only by clean-ok:1b -> single-model phrasing
    sec = _section(md, "### HOME-01")
    assert "єдиний оцінений — clean-ok:1b" in sec
    assert "найгірше" not in sec
    # HOME-03 is scored by fail-model:7b only in the synthetic run
    sec3 = _section(md, "### HOME-03")
    assert "єдиний оцінений — fail-model:7b" in sec3


def test_near_unsolved_test_qualifier(tmp_path):
    run_id = "UNSOLVED"
    run_dir = os.path.join(str(tmp_path), run_id)
    os.makedirs(run_dir)
    recs = []
    # two models both score 0 on HOME-10 (best across models = 0.0 <= 0.10)
    for tag in ("m-a:1b", "m-b:1b"):
        for i in range(3):
            recs.append(_rec(run_id, tag, "HOME-10", "HOME-10-%02d" % i,
                             "WRONG_ANSWER", "FIELD", 0.0, 0.0, '{"a": 1}'))
        for i in range(3):
            recs.append(_rec(run_id, tag, "HOME-01", "HOME-01-%02d" % i,
                             "OK", None, 1.0, 1.0, '{"a": 1}'))
    with open(os.path.join(run_dir, "results.jsonl"), "w",
              encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(run_dir, "manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump({"run_id": run_id,
                   "start_local": "2026-09-21T15:00:00-05:00",
                   "budget_hours": 1.0}, f, ensure_ascii=False)
    with open(os.path.join(run_dir, "perf.csv"), "w", encoding="utf-8") as f:
        f.write("tag,cold_load_s,ttft_s,prompt_tok_s,gen_tok_s,"
                "vram_peak_mb,offload_ratio,throttle\n")
    assert main([run_id, "--results-root", str(tmp_path)]) == 0
    md = _read_md(run_dir)
    sec = _section(md, "### m-a:1b")
    assert "тест майже не розв'язаний жодною моделлю" in sec
