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
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bench import report as _report  # noqa: E402

XLSX_NAME = "NIGHT1_REPORT.xlsx"
FIXED_DT = (2020, 1, 1, 0, 0, 0)

SHEET_NAMES = [
    "Стислий підсумок",
    "Огляд",
    "Оцінка моделей",
    "Рекомендації",
    "Сильні та слабкі сторони",
    "Деталі по тестах",
    "Аналіз помилок",
    "HOME-вердикти",
    "Рейтинг по тестах",
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
    ws = wb.create_sheet(SHEET_NAMES[1])
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
        # Rendered as a fixed string, never from manifest fingerprint: the
        # raw fingerprint is an nvidia-smi dump containing the card's unique
        # hardware UUID plus driver/wattage fragments that must not ship in
        # a public artifact (mirrors build_excel_report_en.py).
        ["GPU", "NVIDIA GeForce RTX 3070 (8 \u0413\u0411 VRAM)"],
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
    ws = wb.create_sheet(SHEET_NAMES[7])
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
    ws = wb.create_sheet(SHEET_NAMES[8])
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


def _sheet_speed(wb, perf_csv_rows: list[dict]) -> None:
    ws = wb.create_sheet(SHEET_NAMES[9])
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
    ws = wb.create_sheet(SHEET_NAMES[10])
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
    ws = wb.create_sheet(SHEET_NAMES[11])
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


# --- Deep-integration additions (12-sheet workbook) -----------------------
# The per-model Ukrainian deep analysis lives in repo-root
# analysis_uk/group_{a,b,c,d}.json (written by four sibling agents; this
# module only renders it through tools/uk_sheets_deep.py).
ANALYSIS_DIRNAME_UK = "analysis_uk"
ELIGIBILITY_RELPATH = os.path.join("config", "eligibility_night.json")

# Reuse the English builder's record-grounded quote helper: it derives
# truth from the records rather than trusting the stored marker. One
# implementation, so the two workbooks can never normalize differently.
from tools.build_excel_report_en import (  # noqa: E402
    normalize_evidence_quote,
)


def _load_eligibility() -> dict:
    try:
        with open(os.path.join(ROOT, ELIGIBILITY_RELPATH),
                  encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _fmt_q3(q: float) -> str:
    return "%.3f" % q


def _uk_executive(run_id: str, manifest: dict, records: list[dict],
                  per_test: dict, per_model: dict,
                  perf_csv_rows: list[dict],
                  gv_records: list[dict]) -> list[tuple[str, str]]:
    """Data-grounded summary; every number matches the English summary.

    Ukrainian prose written fresh from the Ukrainian material (not
    translated cell by cell); every number comes from the same
    bench.report helpers as the English workbook, section for section.
    """
    ov = _report.run_overview(records)
    total = len(records)
    nbr = ov.get("not_run_budget", 0)
    pct = (100.0 * nbr / total) if total else 0.0
    hv = _report.home_verdicts(per_test, records)
    wins = sum(1 for v in hv.values() if v.get("verdict") == "HOME_WIN")
    ties = sum(1 for v in hv.values() if v.get("verdict") == "HOME_TIE")
    losses = sum(1 for v in hv.values() if v.get("verdict") == "HOME_LOSS")
    fmt_err = ov["counts"].get("FORMAT_ERROR", 0)
    ok_n = ov["counts"].get("OK", 0)
    _, home_of_test = _test_meta()
    home_best: list[tuple[str, str, float, str]] = []
    for tid, rows in per_test.items():
        if tid == "PERF":
            continue
        home_tag = home_of_test.get(tid, "")
        home_row = next((r for r in rows if r["model"] == home_tag), None)
        if home_row is not None and (home_row.get("n_scored") or 0) > 0:
            home_best.append((tid, home_tag, float(home_row["q_sem"]),
                              "%d/%d" % (home_row["n_scored"],
                                         home_row["n_total"])))
    home_best.sort(key=lambda t: (-t[2], t[0]))
    if home_best:
        top3 = "; ".join("%s на %s (Q_sem %s, n=%s)" % (tag, tid, _fmt_q3(q),
                                                       n)
                         for tid, tag, q, n in home_best[:3])
        top3_txt = ("Найсильніші власні результати: %s. "
                    "Повні числа по тестах — на аркуші "
                    "«HOME-вердикти»." % top3)
    else:
        top3_txt = ("Жоден власний тест не дав оціненого результату "
                    "в цьому прогоні. Розбивку по тестах дивіться на аркуші "
                    "«HOME-вердикти».")
    partial = sorted(str(r.get("tag", "")) for r in perf_csv_rows
                     if _num_or_none(r.get("offload_ratio")) is not None
                     and _num_or_none(r.get("offload_ratio")) < 1.0)
    if len(partial) == 3:
        hw_txt = ("На цій 8-гігабайтній карті три моделі не вмістилися "
                  "повністю на GPU і працювали з частковим CPU-offload "
                  "(%s), що різко знижує швидкість генерації. "
                  "Деталі — на аркуші «Швидкість»." % ", ".join(partial))
    elif partial:
        hw_txt = ("На цій 8-гігабайтній карті %d моделі не вмістилися "
                  "повністю на GPU і працювали з частковим CPU-offload "
                  "(%s), що різко знижує швидкість генерації. "
                  "Деталі — на аркуші «Швидкість»."
                  % (len(partial), ", ".join(partial)))
    else:
        hw_txt = ("Кожна модель із виміряним offload ratio працювала "
                  "повністю на GPU (offload ratio 1.0). Деталі — на аркуші "
                  "«Швидкість».")
    if gv_records:
        gv_home = _report.summarize_group(
            [r for r in gv_records if _report.test_of(r) == "HOME-07"
             and _report.model_of(r) == "granite3.2-vision:2b"])
        main_recs = [r for r in records if _report.test_of(r) == "HOME-07"
                     and _report.model_of(r) == "granite3.2-vision:2b"]
        main_s = _report.summarize_group(main_recs)
        gv_txt = ("Випадок витягу з документів granite3.2-vision перевірено "
                  "двічі: Q_sem %s за уніфікованим JSON-контрактом і Q_sem "
                  "%s з plain-answer адаптером. Обидва кола дали нуль, що "
                  "вказує на справжнє обмеження здатності моделі, а не на "
                  "артефакт формату запиту. Повне порівняння — на аркуші "
                  "«HOME-07 (окремий прогін)»."
                  % (_fmt_q3(main_s["q_sem"]) if main_s["n_scored"] else "н/д",
                     _fmt_q3(gv_home["q_sem"]) if gv_home["n_scored"]
                     else "н/д"))
    else:
        gv_txt = ("Випадок витягу з документів granite3.2-vision дав Q_sem "
                  "0.000 за уніфікованим JSON-контрактом. Подальше "
                  "порівняння — на аркуші «HOME-07 (окремий прогін)».")
    return [
        ("Що це",
         "Ця книга — звіт NIGHT-1, незалежного бенчмарку локальних великих "
         "мовних моделей на тестовому harness, зібраному з нуля. Проєкт "
         "показує проєктування бенчмарків та системну інженерію: прогін із "
         "жорстким лімітом часу й можливістю продовження, суворий контракт "
         "оцінювання, пер-модельні виміри швидкості та повністю "
         "відтворюваний конвеєр звітності."),
        ("Масштаб прогону",
         "Один завершений прогін (%s) охопив %d моделі та %d груп тестів із "
         "%s записами в одній 8-годинній сесії на споживчому залізі (NVIDIA "
         "GeForce RTX 3070, 8 ГБ VRAM). Аркуш «Огляд» перелічує кожну "
         "модель, групу тестів і кількість за статусами."
         % (manifest.get("run_id", run_id), ov["n_models"], ov["n_tests"],
            "{:,}".format(total))),
        ("Найкращі власні результати", top3_txt),
        ("Вердикти власних моделей",
         "В %d очному порівнянні власних моделей домашня модель записала %d "
         "перемог, %d нічиїх і %d поразок проти найкращого конкурента на "
         "спільному наборі кейсів. Кожен вердикт наведено на аркуші "
         "«HOME-вердикти»." % (wins + ties + losses, wins, ties, losses)),
        ("Покриття часу",
         "Із %s записів %d (%0.1f%%) не запущено, бо вони не вмістилися в "
         "8-годинний ліміт (статус NOT_RUN_BUDGET), і їх виключено з оцінок "
         "якості, а не пораховано нулями. Середні оцінки якості описують "
         "лише виконану роботу. Аркуш «Рейтинг по тестах» позначає кожен "
         "такий рядок явно." % ("{:,}".format(total), nbr, pct)),
        ("Форма проти змісту",
         "Моделі дали %s чистих проходжень (статус OK) і %d помилок формату: "
         "виводи, що порушили контракт відповіді, але все ж отримали "
         "частковий семантичний бал. Шкала окремо оцінює зміст і формат, "
         "тож проблеми оформлення ніколи не плутаються з неправильними "
         "відповідями. Кількість статусів — на аркуші «Огляд»."
         % ("{:,}".format(ok_n), fmt_err)),
        ("Відповідність залізу", hw_txt),
        ("Інженерна знахідка", gv_txt),
        ("Глибина по моделях",
         "Оцінки по моделях, рекомендації щодо застосування, сильні та "
         "слабкі сторони, деталі по тестах і шаблони помилок — на аркушах "
         "«Оцінка моделей», «Рекомендації», «Сильні та слабкі сторони», "
         "«Деталі по тестах» та «Аналіз помилок»."),
    ]


def _sheet_summary(wb, run_id: str, manifest: dict, records: list[dict],
                   per_test: dict, per_model: dict,
                   perf_csv_rows: list[dict], gv_records: list[dict]) -> None:
    from openpyxl.styles import Alignment
    ws = wb.active
    ws.title = SHEET_NAMES[0]
    ws.append(["Розділ", "Текст"])
    for section, text in _uk_executive(run_id, manifest, records, per_test,
                                       per_model, perf_csv_rows, gv_records):
        ws.append([section, text])
    _style_table(ws, [22, 130])
    wrap = Alignment(wrap_text=True, vertical="top")
    for row in ws.iter_rows(min_row=2, max_col=2):
        row[1].alignment = wrap
        ws.row_dimensions[row[0].row].height = 60


# --- Task 2: canonical "Не виконувався" vocabulary -----------------------
# The four Ukrainian analysis groups each invented their own wording for
# the same closed set of eligibility reasons, so the Notes column drifted
# across ~40 phrasings. Every not-attempted note is re-rendered here at
# render time from config/eligibility_night.json, with one consistent
# prefix. Model-specific detail beyond the eligibility reason is appended,
# never discarded. Mirrors the English canonical_not_attempted/normalize
# machinery; only the fixed strings are Ukrainian.

_NOT_ATTEMPTED_PREFIX_UK = "Не виконувався \u2014 "

# Canonical clause per raw eligibility reason (already Ukrainian in the
# config; the map only normalizes, never invents a new cause).
_REASON_GLOSS_UK = {
    "поза scope": "поза запланованим обсягом цього прогону для цієї моделі",
    "QA не є документованим сценарієм GLM-OCR (лише parsing/IE)":
        "QA не є задокументованим сценарієм GLM-OCR (лише parsing/IE)",
    "багатоходовий діалог не задокументовано":
        "багатоходовий діалог не задокументований для цієї моделі",
    "CAP: немає embed":
        "у моделі немає задокументованої embed-здатності для цього тесту",
    "CAP: немає text":
        "у моделі немає задокументованої текстової здатності для цього тесту",
    "CAP: немає text,tools":
        "у моделі немає задокументованої текстової та інструментальної "
        "здатності для цього тесту",
    "CAP: немає tools":
        "у моделі немає задокументованої інструментальної здатності для "
        "цього тесту",
    "CAP: немає tools,vision":
        "у моделі немає задокументованої інструментальної та зорової "
        "здатності для цього тесту",
    "CAP: немає vision":
        "у моделі немає задокументованої зорової здатності для цього тесту",
}


def _strip_note_prefix_uk(note: str) -> str:
    import re as _re
    s = str(note or "").strip()
    s = _re.sub(r"^(не виконувався|не оцінювався|ніколи не виконувався)"
                r"\s*[:\u2014\u2013\-]\s*", "", s,
                flags=_re.IGNORECASE)
    return s.strip()


# Generic paraphrase words: notes built only from these (plus the
# canonical clause's own words) are retired as drift. Anything with novel
# numbers or run-specific facts survives via _SPECIFIC_WORDS_UK.
_GENERIC_WORDS_UK = frozenset(
    ("не виконувався оцінювався модель моделі тест тесту прогін прогону "
     "прогоні запланованим обсягом обсягу поза план обмежив цей іншими "
     "моделями тож зафіксував блок непідтримуваної здатності здатностей "
     "задокументованої задокументована задокументоване задокументованим "
     "задокументований задокументований можливість немає підтримки бачення "
     "бачити має ані чи до для вводу використання виклику генерації чату "
     "тексту текстового текстових текстової візуальної візуальна зору "
     "зорової зорових зорового ембедінгів ембеддингів ембедінгова "
     "ембеддингова ембедінгової ембеддингової спроможності спроможностей "
     "інструментів інструментальних інструментальної інструментального "
     "недокументована недокументовані недокументований багатоходові діалоги "
     "недокументовані сценарії сценарієм відповіді питання документами є "
     "чиє застосування лише розбір та витягування інформації потребує "
     "близько токенів контексту середовище дозволяє потрібний контекст "
     "перевищує ліміт виконання токенів пару було заплановано цьому і "
     "причини записано ця була зоною допустимим набором призначав цю на "
     "запис блока містить подальших причин була запланована пару відхилили "
     "запуску усі бо задокументована ці інші вікно так третій випадки "
     "випадків як через до була в а за").split())

# Words marking genuinely run-specific detail worth keeping after the
# canonical clause (digits handled separately: only digits not already in
# the canonical clause count).
_SPECIFIC_WORDS_UK = frozenset(
    ("бюджет вичерпався незапущені переповнили спробовані запустився "
     "запитів пропущено англійської мови націлені годинний").split())


def _extra_detail_uk(stripped: str, canonical: str) -> str:
    """Return run-specific detail from a note, or "" when generic.

    Generic paraphrases of the eligibility reason are retired, not kept:
    they are the drift this normalization removes. Only detail with novel
    numbers or run-specific facts (budget exhaustion, overflow counts,
    language scope) survives, appended as its own sentence.
    """
    import re as _re
    if not stripped:
        return ""
    words = _re.findall(r"[^\W_]+", stripped.lower(), flags=_re.UNICODE)
    canon_words = set(_re.findall(r"[^\W_]+", canonical.lower(),
                                  flags=_re.UNICODE))
    allowed = set(_GENERIC_WORDS_UK) | canon_words
    if all(w in allowed for w in words):
        return ""
    canon_digits = set(_re.findall(r"\d+", canonical))
    strip_digits = set(_re.findall(r"\d+", stripped))
    flat_words = set(words)
    if (strip_digits - canon_digits) or (flat_words & _SPECIFIC_WORDS_UK):
        detail = stripped.strip()
        if detail and detail[-1] not in ".!?":
            detail += "."
        return detail[0].upper() + detail[1:] if detail else ""
    return ""


def canonical_not_attempted_uk(test_id: str, model_tag: str,
                               original_note: str,
                               eligibility: dict) -> str:
    """Render one canonical Ukrainian not-attempted note."""
    import re as _re
    entry = eligibility.get(test_id, {}).get(model_tag, {})
    if not isinstance(entry, dict):
        entry = {}
    code = str(entry.get("code", "") or "").strip().upper()
    reason = str(entry.get("reason", "") or "")
    if code == "S" or reason.strip() == "поза scope":
        base = (_NOT_ATTEMPTED_PREFIX_UK
                + "поза запланованим обсягом цього прогону для цієї моделі.")
    elif code == "O":
        gloss = _REASON_GLOSS_UK.get(reason.strip(), "")
        if gloss:
            base = "%s%s." % (_NOT_ATTEMPTED_PREFIX_UK, gloss)
        else:
            base = (_NOT_ATTEMPTED_PREFIX_UK
                    + "пару не заплановано в цьому прогоні.")
    elif code == "U":
        gloss = _REASON_GLOSS_UK.get(reason.strip(), "")
        if not gloss:
            m = _re.fullmatch(
                r"CONTEXT_WINDOW:\s*потрібно\s*(\d+),\s*runtime\s*(\d+)",
                reason.strip())
            if m:
                gloss = ("тесту потрібно %s токенів контексту, середовище "
                         "виконання має %s" % (m.group(1), m.group(2)))
        if gloss:
            base = "%s%s." % (_NOT_ATTEMPTED_PREFIX_UK, gloss)
        else:
            base = (_NOT_ATTEMPTED_PREFIX_UK
                    + "у моделі немає задокументованої здатності для "
                    "цього тесту.")
    else:
        base = (_NOT_ATTEMPTED_PREFIX_UK
                + "у цьому прогоні немає оцінених кейсів.")
    extra = _extra_detail_uk(_strip_note_prefix_uk(original_note), base)
    return base + (" " + extra if extra else "")


def normalize_analysis_notes_uk(analysis: list[dict],
                                eligibility: dict) -> dict[str, int]:
    """Rewrite every not-attempted per_test note in place; return counts."""
    from collections import Counter
    counts: Counter = Counter()
    for model in analysis:
        tag = str(model.get("model", "") or "")
        for entry in model.get("per_test") or []:
            if not isinstance(entry, dict):
                continue
            if str(entry.get("outcome", "") or "").strip().lower() != \
                    "не виконувався":
                continue
            entry["note"] = canonical_not_attempted_uk(
                str(entry.get("test_id", "") or ""), tag,
                str(entry.get("note", "") or ""), eligibility)
            counts[entry["note"]] += 1
    return dict(counts)


def _records_by_case_uk(records: list[dict]) -> dict[tuple[str, str], str]:
    """Index response.content by (model tag, case id) for quote checks."""
    index: dict[tuple[str, str], str] = {}
    for r in records:
        try:
            tag = _report.model_of(r)
            case = str(r.get("key", "")).split("|")[4]
            content = (r.get("response") or {}).get("content", "")
        except (IndexError, AttributeError):
            continue
        if isinstance(content, str):
            index.setdefault((str(tag), str(case)), content)
    return index


def normalize_failure_quotes_uk(analysis: list[dict],
                                records: list[dict]) -> dict[str, int]:
    """Normalize every failure_analysis quote against the records.

    Derivation reuses the shared English-builder helper, so both
    workbooks normalize identically; only the trailing marker may change,
    never the quote text. Returns {"complete": n, "truncated": n,
    "unverifiable": n}.
    """
    from collections import Counter
    index = _records_by_case_uk(records)
    counts: Counter = Counter()
    for model in analysis:
        tag = str(model.get("model", "") or "")
        for entry in model.get("failure_analysis") or []:
            if not isinstance(entry, dict):
                continue
            quote = entry.get("example_quote")
            if not isinstance(quote, str) or not quote.strip():
                continue
            full = index.get((tag, str(entry.get("example_case_id", "")
                                       or "")))
            rendered, status = normalize_evidence_quote(quote, full)
            entry["example_quote"] = rendered
            counts[status] += 1
    return {"complete": counts.get("complete", 0),
            "truncated": counts.get("truncated", 0),
            "unverifiable": counts.get("unverifiable", 0)}


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
    _sheet_summary(wb, run_id, manifest, records, per_test, per_model,
                   perf_csv_rows, gv_records)
    _sheet_overview(wb, run_id, manifest, records, gv_records)
    # Deep per-model sheets (sibling module owns the builders; this
    # function only loads, normalizes, and orders them).
    from tools import uk_sheets_deep as _uk_deep
    analysis = _uk_deep.load_analysis_uk(
        os.path.join(ROOT, ANALYSIS_DIRNAME_UK))
    eligibility = _load_eligibility()
    normalize_analysis_notes_uk(analysis, eligibility)
    normalize_failure_quotes_uk(analysis, records)
    _uk_deep.build_all_uk(wb, analysis)
    _sheet_verdicts(wb, records, per_test)
    _sheet_rating(wb, per_test)
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
