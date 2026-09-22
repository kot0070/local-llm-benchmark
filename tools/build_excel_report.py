"""Consolidated Excel workbook for a NIGHT-1 run. Stdlib + openpyxl only.

Reads results/<run_id>/results.jsonl + perf.csv + manifest.json (plus the
supplementary results/<run_id>_gv/results.jsonl for HOME-07 / granite3.2-vision
plain-answer adapter, when present) and writes
results/<run_id>/NIGHT1_REPORT.xlsx.

Every number comes from the records through bench.report helpers
(load_records, compute_tables, summarize_group, home_verdicts, run_overview);
this tool does no scoring arithmetic of its own. MASTER_PLAN.md section 5 is
read at runtime for the "known behaviours" sheet. Never contacts Ollama.

Determinism: workbook properties use a fixed timestamp and the .xlsx zip
entries are rewritten with a fixed date_time, so two runs on the same input
produce byte-identical bytes.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import zipfile
from collections import Counter
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bench import report as _report  # noqa: E402

XLSX_NAME = "NIGHT1_REPORT.xlsx"
FIXED_DT = (2020, 1, 1, 0, 0, 0)

SHEET_NAMES = [
    "Огляд",
    "HOME-вердикти",
    "Рейтинг по тестах",
    "Профілі моделей",
    "Сильні та слабкі сторони",
    "Швидкість",
    "Відомі особливості",
    "HOME-07 (окремий прогін)",
]

VERDICT_UA = {
    "HOME_WIN": "перемагає",
    "HOME_TIE": "нічия",
    "HOME_LOSS": "програє",
}
NO_DATA = "недостатньо даних"
# F9: missing gen tok/s uses the same wording as OWNER_SUMMARY_UK.md /
# ANALYSIS_UK.md ("немає даних"), not this workbook's generic NO_DATA.
NO_GEN_DATA = "немає даних"
RANKED = "у рейтингу"
NOT_RANKED = "поза рейтингом"


def _resolve_run_dir(run_id: str, results_root: str | None) -> str:
    if os.path.isdir(run_id):
        return os.path.abspath(run_id)
    base = results_root or os.path.join(ROOT, "results")
    if not os.path.isabs(base):
        base = os.path.join(ROOT, base)
    return os.path.join(base, run_id)


def _load_manifest(run_dir: str) -> dict:
    try:
        with open(os.path.join(run_dir, "manifest.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _load_perf(run_dir: str) -> list[dict]:
    path = os.path.join(run_dir, "perf.csv")
    rows: list[dict] = []
    try:
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                rows.append({k: (v.strip() if isinstance(v, str) else v)
                             for k, v in row.items()})
    except OSError:
        return []
    return rows


def _parse_iso(s: str):
    try:
        return datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def _run_times(manifest: dict, records: list[dict]):
    start = _parse_iso(manifest.get("start_local") or manifest.get("start_utc") or "")
    end = None
    for r in records:
        ts = r.get("timestamps") or {}
        t = _parse_iso(ts.get("local") or ts.get("utc") or "")
        if t is not None and (end is None or t > end):
            end = t
    return start, end


def _test_meta() -> tuple[dict, dict]:
    """Return ({test_id: title}, {test_id: home_tag}); {}s on failure."""
    try:
        from bench import registry as _reg
        tdir = os.path.join(ROOT, "bench", "tests")
        mods = _reg.discover(tdir)
        titles = {tid: str(getattr(m.META, "get", lambda *a: "")("title", ""))
                  if isinstance(m.META, dict) else "" for tid, m in mods.items()}
        home_map = _reg.home_model_map(mods)  # {model_tag: test_id}
        inv = {v: k for k, v in home_map.items()}
        return titles, inv
    except Exception:
        return {}, {}


def _known_behaviours() -> list[str]:
    """Bullet lines of MASTER_PLAN.md section 5, read at runtime."""
    path = os.path.join(ROOT, "MASTER_PLAN.md")
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    start = next((i for i, ln in enumerate(lines)
                  if ln.startswith("## 5.")), None)
    if start is None:
        return []
    out = []
    for ln in lines[start + 1:]:
        if ln.startswith("## "):
            break
        if ln.startswith("- "):
            out.append(ln)
    return out


def _only_status(row: dict, statuses: set) -> bool:
    counts = row.get("counts") or {}
    return bool(counts) and set(counts) <= statuses


def _is_not_ranked(row: dict) -> bool:
    if _only_status(row, {"UNSUPPORTED_CAPABILITY"}):
        return True
    if (_only_status(row, {"NOT_RUN_BUDGET", "UNSUPPORTED_CAPABILITY"})
            and not _only_status(row, {"UNSUPPORTED_CAPABILITY"})):
        return True
    return False


def _num_or_none(v):
    try:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _verdict_sub_reason(v: dict) -> str:
    det = v.get("details") or {}
    return str(v.get("sub_reason") or det.get("sub_reason") or "-")


# ---------------------------------------------------------------- formatting

def _style_table(ws, widths: list[float], numfmt: dict[int, str] | None = None):
    from openpyxl.styles import Font
    bold = Font(bold=True)
    for cell in ws[1]:
        cell.font = bold
    ws.freeze_panes = "A2"
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    if numfmt:
        for row in ws.iter_rows(min_row=2):
            for col_idx, fmt in numfmt.items():
                cell = row[col_idx]
                if isinstance(cell.value, (int, float)):
                    cell.number_format = fmt


def _save_deterministic(wb, path: str) -> None:
    from datetime import datetime as _dt
    import re as _re
    props = wb.properties
    props.created = _dt(*FIXED_DT)
    props.modified = _dt(*FIXED_DT)
    props.creator = "BENCH_V5_NIGHT"
    props.lastModifiedBy = "BENCH_V5_NIGHT"
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    zin = zipfile.ZipFile(buf, "r")
    # openpyxl stamps docProps/core.xml dcterms:modified with the current
    # time at save (ignoring wb.properties); pin both timestamps so the
    # bytes are stable across runs.
    fixed_ts = b"2020-01-01T00:00:00Z"
    tmp = path + ".tmpzip"
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "docProps/core.xml":
                data = _re.sub(
                    rb"<dcterms:created[^>]*>[^<]*</dcterms:created>",
                    rb'<dcterms:created xsi:type="dcterms:W3CDTF">'
                    + fixed_ts + rb"</dcterms:created>", data)
                data = _re.sub(
                    rb"<dcterms:modified[^>]*>[^<]*</dcterms:modified>",
                    rb'<dcterms:modified xsi:type="dcterms:W3CDTF">'
                    + fixed_ts + rb"</dcterms:modified>", data)
            zi = zipfile.ZipInfo(item.filename, date_time=FIXED_DT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zout.writestr(zi, data)
    zin.close()
    os.replace(tmp, path)


# ---------------------------------------------------------------- sheets

def _sheet_overview(wb, run_id: str, manifest: dict, records: list[dict],
                    gv_records: list[dict]) -> None:
    ws = wb.active
    ws.title = SHEET_NAMES[0]
    ov = _report.run_overview(records)
    start, end = _run_times(manifest, records)
    fp = manifest.get("fingerprint") or {}
    total = len(records)
    nbr = ov.get("not_run_budget", 0)
    pct = (100.0 * nbr / total) if total else 0.0
    rows: list[list] = [
        ["run_id", manifest.get("run_id", run_id)],
        ["початок (local)", manifest.get("start_local", "") or ""],
        ["кінець (local)", end.isoformat() if end is not None else ""],
        ["тривалість, хв",
         round((end - start).total_seconds() / 60.0, 1)
         if (start is not None and end is not None and end >= start) else ""],
        ["бюджет, год", manifest.get("budget_hours", "")],
        ["Ollama", manifest.get("ollama_version", "")],
        ["GPU", fp.get("gpu", "") or ""],
        ["моделей запущено", ov["n_models"]],
        ["моделі", ", ".join(ov["models"])],
        ["тестів запущено", ov["n_tests"]],
        ["тести", ", ".join(ov["tests"])],
        ["записів", total],
        ["NOT_RUN_BUDGET", nbr],
        ["NOT_RUN_BUDGET, %", round(pct, 1)],
        ["", ""],
        ["Статус", "Кількість"],
    ]
    for st in sorted(ov["counts"]):
        rows.append([st, ov["counts"][st]])
    rows.append(["", ""])
    gv_n = len(gv_records)
    rows.append(["Примітка _gv",
                 "Існує додатковий прогін %s_gv: HOME-07 / granite3.2-vision:2b "
                 "за документованим plain-answer адаптером. Його числа не "
                 "змішуються з таблицями нижче; деталі — на аркуші "
                 "\"HOME-07 (окремий прогін)\"." % manifest.get("run_id", run_id)])
    rows.append(["", ""])
    rows.append(["Блок _gv (окремо, не порівнюється)", ""])
    rows.append(["_gv run_id", "%s_gv" % manifest.get("run_id", run_id)])
    rows.append(["_gv записів", gv_n])
    if gv_records:
        gv_home = _report.summarize_group(
            [r for r in gv_records if _report.test_of(r) == "HOME-07"
             and _report.model_of(r) == "granite3.2-vision:2b"])
        rows.append(["_gv HOME-07 Q_sem",
                     round(gv_home["q_sem"], 3) if gv_home["n_scored"] else ""])
        rows.append(["_gv HOME-07 n",
                     "%d/%d" % (gv_home["n_scored"], gv_home["n_total"])])
    else:
        rows.append(["_gv HOME-07 Q_sem", ""])
        rows.append(["_gv HOME-07 n", ""])
    ws.append(["Поле", "Значення"])
    for r in rows:
        ws.append(r)
    _style_table(ws, [28, 90])


def _sheet_verdicts(wb, records: list[dict], per_test: dict) -> None:
    ws = wb.create_sheet(SHEET_NAMES[1])
    titles, home_of_test = _test_meta()
    hv = _report.home_verdicts(per_test, records)
    ws.append(["Тест", "Назва", "HOME-модель", "HOME Q_sem", "HOME n",
               "Конкурент", "Конкурент Q_sem", "Конкурент n",
               "common_n", "Вердикт"])
    for tid in sorted(_report.HOME_SET):
        rows = per_test.get(tid, [])
        title = titles.get(tid, "")
        home_tag = home_of_test.get(tid, "")
        home_row = next((r for r in rows if r["model"] == home_tag), None)
        v = hv.get(tid)
        if home_row is None or (home_row.get("n_scored") or 0) == 0:
            home_q: object = ""
            home_n = ("" if home_row is None
                      else "%d/%d" % (home_row["n_scored"], home_row["n_total"]))
            comp_tag: object = ""
            comp_q: object = ""
            comp_n = ""
            common: object = ""
            verdict = NO_DATA
            if v is not None and v.get("second"):
                comp_tag = v["second"]
                comp_r = next((r for r in rows if r["model"] == comp_tag), None)
                if comp_r is not None and (comp_r.get("n_scored") or 0) > 0:
                    comp_q = round(comp_r["q_sem"], 3)
                    comp_n = "%d/%d" % (comp_r["n_scored"], comp_r["n_total"])
                common = v.get("common_n", "")
            ws.append([tid, title, home_tag or NO_DATA, home_q, home_n,
                       comp_tag, comp_q, comp_n, common, verdict])
            continue
        home_q = round(home_row["q_sem"], 3)
        home_n = "%d/%d" % (home_row["n_scored"], home_row["n_total"])
        ranked = sorted((r for r in rows if not _is_not_ranked(r)),
                        key=lambda r: (-r["q_sem"], -r["n_scored"], r["model"]))
        comp_row = next((r for r in ranked if r["model"] != home_tag), None)
        if v is not None and v.get("second"):
            comp_tag = v["second"]
            comp_r = next((r for r in rows if r["model"] == comp_tag), comp_row)
            if comp_r is not None and (comp_r.get("n_scored") or 0) > 0:
                comp_q = round(comp_r["q_sem"], 3)
                comp_n = "%d/%d" % (comp_r["n_scored"], comp_r["n_total"])
            else:
                comp_q, comp_n = "", ""
            verdict = VERDICT_UA.get(v.get("verdict", ""), NO_DATA)
            common = v.get("common_n", "")
        elif comp_row is not None:
            comp_tag = comp_row["model"]
            comp_q = round(comp_row["q_sem"], 3)
            comp_n = "%d/%d" % (comp_row["n_scored"], comp_row["n_total"])
            common, verdict = "", NO_DATA
        else:
            comp_tag, comp_q, comp_n, common, verdict = (
                NO_DATA, "", "", "", NO_DATA)
        ws.append([tid, title, home_tag, home_q, home_n,
                   comp_tag, comp_q, comp_n, common, verdict])
    _style_table(ws, [10, 30, 24, 12, 12, 24, 14, 12, 10, 14],
                 {3: "0.000", 6: "0.000"})


def _sheet_rating(wb, per_test: dict) -> None:
    ws = wb.create_sheet(SHEET_NAMES[2])
    ws.append(["Тест", "Модель", "Q_sem", "Q_strict", "n_scored", "n_total",
               "coverage", "CI low", "CI high", "Покриття < 0.9",
               "Статус рейтингу"])
    for tid in sorted(t for t in per_test if t != "PERF"):
        rows = per_test[tid]
        ranked = sorted((r for r in rows if not _is_not_ranked(r)),
                        key=lambda r: (-r["q_sem"], -r["n_scored"], r["model"]))
        rest = sorted((r for r in rows if _is_not_ranked(r)),
                      key=lambda r: r["model"])
        for r in ranked + rest:
            low_cov = "так" if r.get("coverage", 1.0) < 0.9 else "ні"
            status = NOT_RANKED if r in rest else RANKED
            ws.append([tid, r["model"], round(r["q_sem"], 3),
                       round(r["q_strict"], 3), r["n_scored"], r["n_total"],
                       round(r.get("coverage", 0.0), 3),
                       round(r["ci_lo"], 3), round(r["ci_hi"], 3),
                       low_cov, status])
    _style_table(ws, [10, 24, 10, 10, 10, 10, 10, 10, 10, 13, 15],
                 {2: "0.000", 3: "0.000", 6: "0.0%", 7: "0.000", 8: "0.000"})


def _sheet_profiles(wb, records: list[dict], per_model: dict,
                    perf_csv_rows: list[dict]) -> None:
    ws = wb.create_sheet(SHEET_NAMES[3])
    ws.append(["Модель", "HOME-тест", "HOME Q_sem", "HOME n",
               "Тестів (без PERF)", "Середній Q_sem", "Топ-невдачі (2)",
               "gen tok/s"])
    try:
        from bench import registry as _reg
        mods = _reg.discover(os.path.join(ROOT, "bench", "tests"))
        home_of_model = _reg.home_model_map(mods)
    except Exception:
        home_of_model = {}
    fail_reasons: dict[str, Counter] = {}
    for r in records:
        v = _report.verdict_of(r)
        if v.get("status") not in ("OK",):
            tag = _report.model_of(r)
            key = "%s[%s]" % (v.get("status", "?"), _verdict_sub_reason(v))
            fail_reasons.setdefault(tag, Counter())[key] += 1
    perf_by_tag = {str(row.get("tag", "")): row for row in perf_csv_rows}
    for tag in sorted(per_model):
        tests = {t: s for t, s in per_model[tag]["tests"].items() if t != "PERF"}
        n_tests = len(tests)
        scored = [s for s in tests.values() if (s.get("n_scored") or 0) > 0]
        mean: object = (round(sum(s["q_sem"] for s in scored) / len(scored), 3)
                        if scored else "")
        home_tid = home_of_model.get(tag, "")
        home_s = tests.get(home_tid)
        if home_s is None:
            home_q: object = ""
            home_n = ""
        elif (home_s.get("n_scored") or 0) == 0:
            home_q = ""
            home_n = "%d/%d" % (home_s["n_scored"], home_s["n_total"])
        else:
            home_q = round(home_s["q_sem"], 3)
            home_n = "%d/%d" % (home_s["n_scored"], home_s["n_total"])
        top = fail_reasons.get(tag, Counter()).most_common(2)
        fail_txt = "; ".join("%s (x%d)" % (k, n) for k, n in top) if top else "немає"
        gen: object = NO_GEN_DATA
        prow = perf_by_tag.get(tag)
        if prow is not None:
            g = _num_or_none(prow.get("gen_tok_s"))
            gen = round(g, 1) if g is not None else NO_GEN_DATA
        ws.append([tag, home_tid, home_q, home_n, n_tests, mean, fail_txt, gen])
    _style_table(ws, [24, 12, 12, 10, 14, 13, 44, 11],
                 {2: "0.000", 5: "0.000", 7: "0.0"})


STRONG_HEADER = ["Модель", "Сильні сторони", "Слабкі сторони",
                   "Рекомендація для цього заліза (RTX 3070 8 ГБ)", "Джерело"]
STRONG_NONE = "немає вираженних сильних сторін у цьому прогоні"
WEAK_NONE = "суттєвих слабких сторін у цьому прогоні не виявлено"


def _fmt_q(q: float) -> str:
    return "%.3f" % q


def _sheet_strengths(wb, records: list[dict], per_model: dict,
                     perf_csv_rows: list[dict]) -> None:
    """Per-model strengths/weaknesses + RTX 3070 8GB recommendation.

    Every bullet is derived from this run's own records (via bench.report
    summaries), perf.csv numbers, or MASTER_PLAN section 5 context already
    surfaced in ANALYSIS_UK.md. No general priors about model families.
    Cells in one column are joined with "; " consistently.
    """
    from openpyxl.styles import Alignment
    ws = wb.create_sheet(SHEET_NAMES[4])
    ws.append(STRONG_HEADER)
    try:
        from bench import registry as _reg
        mods = _reg.discover(os.path.join(ROOT, "bench", "tests"))
        home_of_model = _reg.home_model_map(mods)
    except Exception:
        home_of_model = {}
    scored_fails: dict[str, Counter] = {}
    ok_count: dict[str, int] = {}
    scored_count: dict[str, int] = {}
    notrun_count: dict[str, int] = {}
    for r in records:
        tag = _report.model_of(r)
        st = _report.verdict_of(r).get("status", "?")
        if st in _report.SCORED:
            scored_count[tag] = scored_count.get(tag, 0) + 1
            if st == "OK":
                ok_count[tag] = ok_count.get(tag, 0) + 1
            else:
                key = "%s[%s]" % (st, _verdict_sub_reason(
                    _report.verdict_of(r)))
                scored_fails.setdefault(tag, Counter())[key] += 1
        elif st == "NOT_RUN_BUDGET":
            notrun_count[tag] = notrun_count.get(tag, 0) + 1
    perf_by_tag = {str(row.get("tag", "")): row for row in perf_csv_rows}
    for tag in sorted(per_model):
        tests = {t: s for t, s in per_model[tag]["tests"].items()
                 if t != "PERF"}
        scored = {t: s for t, s in tests.items()
                  if (s.get("n_scored") or 0) > 0}
        n_sc = scored_count.get(tag, 0)
        n_ok = ok_count.get(tag, 0)
        ok_rate = (n_ok / n_sc) if n_sc else 0.0
        mean: float | None = (sum(s["q_sem"] for s in scored.values())
                              / len(scored)) if scored else None
        home_tid = home_of_model.get(tag, "")
        home_s = tests.get(home_tid) if home_tid else None
        home_q: float | None = None
        home_n = ""
        if home_s is not None and (home_s.get("n_scored") or 0) > 0:
            home_q = float(home_s["q_sem"])
            home_n = "%d/%d" % (home_s["n_scored"], home_s["n_total"])
        best_tid, best_q, best_n = "", None, ""
        worst_tid, worst_q = "", None
        if scored:
            ordered = sorted(scored.items(),
                             key=lambda kv: (-kv[1]["q_sem"],
                                             -(kv[1].get("n_scored") or 0),
                                             kv[0]))
            best_tid = ordered[0][0]
            best_q = float(ordered[0][1]["q_sem"])
            best_n = "%d/%d" % (ordered[0][1]["n_scored"],
                                ordered[0][1]["n_total"])
            ordered_w = sorted(scored.items(),
                               key=lambda kv: (kv[1]["q_sem"],
                                               -(kv[1].get("n_scored") or 0),
                                               kv[0]))
            worst_tid = ordered_w[0][0]
            worst_q = float(ordered_w[0][1]["q_sem"])
        prow = perf_by_tag.get(tag, {})
        gen = _num_or_none(prow.get("gen_tok_s"))
        cold = _num_or_none(prow.get("cold_load_s"))
        off = _num_or_none(prow.get("offload_ratio"))
        # ---- strengths (fixed priority order, max 4)
        s: list[str] = []
        if home_q is not None and home_q >= 0.7:
            s.append("Власний тест %s: Q_sem %s (n=%s)" % (
                home_tid, _fmt_q(home_q), home_n))
        if best_q is not None and best_q >= 0.8 and best_tid != home_tid:
            s.append("Найкращий результат %s: Q_sem %s (n=%s)" % (
                best_tid, _fmt_q(best_q), best_n))
        if mean is not None and mean >= 0.8 and len(scored) >= 3:
            s.append("Середній Q_sem %s по %d оцінених тестах" % (
                _fmt_q(mean), len(scored)))
        if n_sc and ok_rate >= 0.8 and n_sc >= 20:
            s.append("Висока частка OK: %d з %d (%.1f%%)" % (
                n_ok, n_sc, 100.0 * ok_rate))
        if gen is not None and gen >= 100.0:
            s.append("Швидка генерація %.1f ток/с (perf.csv)" % gen)
        if off is not None and off >= 1.0 and gen is not None:
            s.append("Повний GPU offload (1.0) — вміщується у 8 ГБ VRAM")
        if n_sc >= 10 and not scored_fails.get(tag):
            s.append("Чиста відповідність формату: 0 FORMAT_ERROR на %d "
                     "оцінених записах" % n_sc)
        elif (n_sc >= 10 and scored_fails.get(tag)
                and not any(k.startswith("FORMAT_ERROR")
                            for k in scored_fails[tag])):
            s.append("Чиста відповідність формату: 0 FORMAT_ERROR на %d "
                     "оцінених записах" % n_sc)
        strengths = "; ".join(s[:4]) if s else STRONG_NONE
        # ---- weaknesses (fixed priority order, max 4)
        w: list[str] = []
        if home_q is not None and home_q <= 0.0:
            s_home_n = home_n
            w.append("Власний тест %s: Q_sem 0.000 (n=%s)" % (
                home_tid, s_home_n))
        elif home_q is not None and home_q < 0.5:
            w.append("Власний тест %s слабкий: Q_sem %s (n=%s)" % (
                home_tid, _fmt_q(home_q), home_n))
        if worst_q is not None and worst_q <= 0.5 and worst_tid != home_tid:
            w.append("Найгірший результат %s: Q_sem %s" % (
                worst_tid, _fmt_q(worst_q)))
        top = scored_fails.get(tag, Counter()).most_common(2)
        hw_issue = ""
        if off is not None and off < 1.0 and gen is not None and gen < 25.0:
            hw_issue = ("Частковий CPU offload (%.3f); повільна генерація "
                        "%.1f ток/с (perf.csv) — не вміщується у 8 ГБ VRAM"
                        % (off, gen))
        elif off is not None and off < 1.0:
            hw_issue = ("Частковий CPU offload (%.3f) — не вміщується у "
                        "8 ГБ VRAM" % off)
        elif gen is not None and gen < 25.0:
            hw_issue = "Повільна генерація %.1f ток/с (perf.csv)" % gen
        if top:
            w.append("%s (x%d)" % (top[0][0], top[0][1]))
        if hw_issue:
            w.append(hw_issue)
        if len(top) > 1:
            w.append("%s (x%d)" % (top[1][0], top[1][1]))
        nr = notrun_count.get(tag, 0)
        if nr >= 10:
            w.append("Покриття неповне: NOT_RUN_BUDGET x%d" % nr)
        weaknesses = "; ".join(w[:4]) if w else WEAK_NONE
        # ---- hardware recommendation (1-2 sentences, always with numbers)
        if gen is not None and cold is not None:
            hw = "cold load %.1f c, %.1f ток/с" % (cold, gen)
        elif cold is not None:
            hw = "cold load %.1f c, швидкості генерації в perf.csv немає" % (
                cold,)
        else:
            hw = "вимірів швидкості в perf.csv немає"
        off_txt = ("offload %.3f (частковий CPU offload)" % off
                   if (off is not None and off < 1.0)
                   else "повний offload (1.0)"
                   if off is not None else "offload не виміряно")
        if len(scored) == 1:
            only_tid = next(iter(scored))
            only_q = float(scored[only_tid]["q_sem"])
            fit = "Єдиний оцінений тест %s (Q_sem %s). " % (
                only_tid, _fmt_q(only_q))
        elif best_q is not None:
            fit = "Найкраще: %s (Q_sem %s); власний %s: %s. " % (
                best_tid, _fmt_q(best_q),
                home_tid if home_tid else "-",
                _fmt_q(home_q) if home_q is not None else "немає оцінки")
        else:
            fit = "Оцінених тестів немає. "
        if off is not None and off < 1.0:
            verdict = ("На RTX 3070 8 ГБ (%s; %s): практичний вибір лише "
                       "коли якість на конкретній задачі виправдовує "
                       "очікування, інакше краще швидша модель з повним "
                       "offload." % (hw, off_txt))
        elif best_q is not None and best_q >= 0.9 and gen is not None \
                and gen >= 70.0:
            verdict = ("На RTX 3070 8 ГБ (%s; %s): розумний вибір для "
                       "%s-подібних задач." % (hw, off_txt, best_tid))
        elif home_q is not None and home_q >= 0.8:
            verdict = ("На RTX 3070 8 ГБ (%s; %s): розумний вибір для "
                       "%s." % (hw, off_txt, home_tid))
        elif home_q is not None and home_q <= 0.0 and home_tid:
            verdict = ("На RTX 3070 8 ГБ (%s; %s): для %s не рекомендується; "
                       "розглядати лише під задачі з високим Q_sem вище." % (
                           hw, off_txt, home_tid))
        else:
            verdict = ("На RTX 3070 8 ГБ (%s; %s): обирати під задачі з "
                       "високим Q_sem вище; для слабких тестів краще "
                       "щось інше." % (hw, off_txt))
        reco = fit + verdict
        # ---- source pointer
        tids = [t for t in (home_tid, best_tid, worst_tid) if t]
        seen: list[str] = []
        for t in tids:
            if t not in seen:
                seen.append(t)
        src = "ANALYSIS_UK.md (%s)%s; perf.csv" % (
            tag, ("; " + ", ".join(seen)) if seen else "")
        ws.append([tag, strengths, weaknesses, reco, src])
    _style_table(ws, [24, 60, 60, 70, 34])
    wrap = Alignment(wrap_text=True, vertical="top")
    for row in ws.iter_rows(min_row=2, max_col=5):
        for cell in row[1:]:
            cell.alignment = wrap
        ws.row_dimensions[row[0].row].height = 75


def _sheet_speed(wb, perf_csv_rows: list[dict]) -> None:
    ws = wb.create_sheet(SHEET_NAMES[5])
    ws.append(["Модель", "cold load, s", "TTFT, s", "prompt tok/s",
               "gen tok/s", "offload ratio"])
    rows = sorted(perf_csv_rows,
                  key=lambda r: (_num_or_none(r.get("gen_tok_s")) is None,
                                 -(_num_or_none(r.get("gen_tok_s")) or 0.0),
                                 str(r.get("tag", ""))))
    for r in rows:
        ws.append([r.get("tag", ""),
                   _num_or_none(r.get("cold_load_s")) or "",
                   _num_or_none(r.get("ttft_s")) or "",
                   _num_or_none(r.get("prompt_tok_s")) or "",
                   _num_or_none(r.get("gen_tok_s"))
                   if _num_or_none(r.get("gen_tok_s")) is not None
                   else NO_GEN_DATA,
                   _num_or_none(r.get("offload_ratio")) or ""])
    ws.append([])
    partial = sorted(str(r.get("tag", "")) for r in rows
                     if _num_or_none(r.get("offload_ratio")) is not None
                     and _num_or_none(r.get("offload_ratio")) < 1.0)
    if partial:
        ws.append(["Примітка: offload_ratio < 1.0 (частковий CPU offload, "
                   "модель не вмістилась у 8 GB VRAM): "
                   + ", ".join(partial)])
    else:
        ws.append(["Примітка: жодна модель з виміряним offload ratio не має "
                   "значення < 1.0 (частковий CPU offload відсутній)."])
    _style_table(ws, [24, 13, 11, 13, 11, 13],
                 {1: "0.00", 2: "0.000", 3: "0.0", 4: "0.0", 5: "0.000"})


def _sheet_behaviours(wb) -> None:
    ws = wb.create_sheet(SHEET_NAMES[6])
    ws.append(["Модель", "Особливість"])
    for bullet in _known_behaviours():
        text = bullet[2:] if bullet.startswith("- ") else bullet
        if ": " in text:
            model, feat = text.split(": ", 1)
            ws.append([model.strip(), feat.strip()])
        else:
            ws.append([text.strip(), ""])
    _style_table(ws, [28, 110])


def _supplementary_note_text(run_dir: str) -> str | None:
    for name in ("HOME-07-supplementary-note.md",):
        path = os.path.join(run_dir, name)
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except OSError:
            continue
    return None


def _sheet_home07(wb, run_dir: str, records: list[dict],
                  gv_records: list[dict]) -> None:
    ws = wb.create_sheet(SHEET_NAMES[7])
    ws.append(["Показник", "Уніфікований JSON-контракт (основний прогін)",
               "Plain-answer адаптер (прогін _gv)"])
    main_recs = [r for r in records if _report.test_of(r) == "HOME-07"
                 and _report.model_of(r) == "granite3.2-vision:2b"]
    gv_recs = [r for r in gv_records if _report.test_of(r) == "HOME-07"
               and _report.model_of(r) == "granite3.2-vision:2b"]
    main_s = _report.summarize_group(main_recs)
    gv_s = _report.summarize_group(gv_recs)
    ws.append(["Q_sem",
               round(main_s["q_sem"], 3) if main_s["n_scored"] else "",
               round(gv_s["q_sem"], 3) if gv_s["n_scored"] else ""])
    ws.append(["Q_strict",
               round(main_s["q_strict"], 3) if main_s["n_scored"] else "",
               round(gv_s["q_strict"], 3) if gv_s["n_scored"] else ""])
    ws.append(["n (scored/total)",
               "%d/%d" % (main_s["n_scored"], main_s["n_total"]),
               "%d/%d" % (gv_s["n_scored"], gv_s["n_total"])])
    ws.append(["Статуси:", "основний", "_gv"])
    for st in sorted(set(main_s["counts"]) | set(gv_s["counts"])):
        ws.append([st, main_s["counts"].get(st, 0), gv_s["counts"].get(st, 0)])
    note = ("Ці два числа отримано за різних умов (уніфікований JSON-контракт "
            "проти plain-answer адаптера) і вони не порівнюються напряму як "
            "один Q_sem.")
    extra = _supplementary_note_text(run_dir)
    if extra:
        first = next((ln.strip() for ln in extra.splitlines() if ln.strip()),
                     "")
        if first:
            note = note + " " + first[:300]
    ws.append(["Примітка", note, ""])
    _style_table(ws, [18, 40, 40], {1: "0.000", 2: "0.000"})


def build_workbook(run_dir: str, out_path: str) -> str:
    import openpyxl
    manifest = _load_manifest(run_dir)
    records = _report.load_records(run_dir)
    perf_csv_rows = _load_perf(run_dir)
    gv_records: list[dict] = []
    gv_dir = run_dir.rstrip(os.sep) + "_gv"
    if os.path.isdir(gv_dir):
        try:
            gv_records = _report.load_records(gv_dir)
        except OSError:
            gv_records = []
    run_id = manifest.get("run_id", os.path.basename(run_dir))
    per_test, per_model, _ = _report.compute_tables(records)
    wb = openpyxl.Workbook()
    _sheet_overview(wb, run_id, manifest, records, gv_records)
    _sheet_verdicts(wb, records, per_test)
    _sheet_rating(wb, per_test)
    _sheet_profiles(wb, records, per_model, perf_csv_rows)
    _sheet_strengths(wb, records, per_model, perf_csv_rows)
    _sheet_speed(wb, perf_csv_rows)
    _sheet_behaviours(wb)
    _sheet_home07(wb, run_dir, records, gv_records)
    _save_deterministic(wb, out_path)
    return out_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build consolidated NIGHT-1 xlsx")
    p.add_argument("run_id", help="run id or path to run dir")
    p.add_argument("--results-root", default=None)
    a = p.parse_args(argv)
    run_dir = _resolve_run_dir(a.run_id, a.results_root)
    out_path = os.path.join(run_dir, XLSX_NAME)
    build_workbook(run_dir, out_path)
    print("excel report written to %s" % out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
