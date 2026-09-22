"""Per-model / per-test analysis (Ukrainian) for a NIGHT-1 run. Stdlib only.

Reads results/<run_id>/results.jsonl + perf.csv + manifest.json (plus the
supplementary results/<run_id>_gv/results.jsonl for the granite3.2-vision:2b /
HOME-07 plain-answer adapter, when present) and writes
results/<run_id>/ANALYSIS_UK.md.

Every number comes from the records (via bench.report helpers); every quoted
example is a verbatim substring of a real response.content; recommendations
follow only from data in the run. Deterministic: sorted ordering everywhere,
no wall-clock reads -- running twice yields byte-identical output.
Never contacts Ollama.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bench import report as _report  # noqa: E402

MD_NAME = "ANALYSIS_UK.md"
QUOTE_LIMIT = 200
# Models with fewer scored records than this get an explicit
# insufficient-data note instead of a usage recommendation.
MIN_SCORED_FOR_REC = 5
INSUFFICIENT = ("Недостатньо даних для відповідальної рекомендації")
NO_DATA = "немає даних"


def _plural_ua(n: int, one: str, few: str, many: str) -> str:
    """Ukrainian numeral-noun agreement: 1 -> one, 2-4 (not 12-14) -> few,
    else -> many (covers 0, 5-20, 11-14, 25-30, ...)."""
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return few
    return many


def _plural_raz(n: int) -> str:
    return _plural_ua(n, "раз", "рази", "разів")


def _plural_zapys(n: int) -> str:
    return _plural_ua(n, "запис", "записи", "записів")


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


def _case_of(rec: dict) -> str:
    key = rec.get("key", "")
    parts = key.split("|")
    if len(parts) >= 5 and parts[4]:
        return parts[4]
    return str(rec.get("case_id", "?") or "?")


def _sub_reason(v: dict) -> str:
    det = v.get("details") or {}
    return str(v.get("sub_reason") or det.get("sub_reason") or "-")


def _status_label(v: dict) -> str:
    sub = _sub_reason(v)
    st = str(v.get("status", "?"))
    return f"{st}[{sub}]" if sub != "-" else st


def _content_of(rec: dict) -> str:
    return str((rec.get("response") or {}).get("content") or "")


def _shorten(text: str, limit: int = QUOTE_LIMIT) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def _home_maps() -> tuple[dict, dict]:
    """Return ({test_id: home_tag}, {home_tag: test_id}); {}s on failure."""
    try:
        from bench import registry as _reg
        mods = _reg.discover(os.path.join(ROOT, "bench", "tests"))
        home_of_model = _reg.home_model_map(mods)
        home_of_test = {v: k for k, v in home_of_model.items()}
        return home_of_test, home_of_model
    except Exception:
        return {}, {}


def _plan_notes_for_test(tid: str, plan_path: str | None = None) -> list[str]:
    """Bullets from MASTER_PLAN.md sections 4/5 that mention this test id.

    A bullet may wrap onto continuation lines in the source file; join those
    lines so the quoted context is a complete sentence, not a mid-sentence
    cut. Selection is unchanged (the test id must appear in the bullet's
    first physical line); only the captured text is extended.
    """
    path = plan_path or os.path.join(ROOT, "MASTER_PLAN.md")
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    i4 = next((i for i, ln in enumerate(lines) if ln.startswith("## 4.")), None)
    if i4 is None:
        return []
    i6 = next((i for i, ln in enumerate(lines)
               if ln.startswith("## 6.") and i > i4), None)
    window = lines[i4 + 1:] if i6 is None else lines[i4 + 1:i6]
    joined: list[tuple[str, str]] = []  # (first line, full joined bullet)
    current_first: str | None = None
    current_parts: list[str] = []
    for ln in window:
        if ln.startswith("- "):
            if current_first is not None:
                joined.append(
                    (current_first, " ".join(" ".join(current_parts).split())))
            current_first = ln
            current_parts = [ln]
        elif current_first is not None:
            stripped = ln.strip()
            if not stripped or ln.startswith("##"):
                joined.append(
                    (current_first, " ".join(" ".join(current_parts).split())))
                current_first = None
                current_parts = []
            else:
                current_parts.append(stripped)
    if current_first is not None:
        joined.append(
            (current_first, " ".join(" ".join(current_parts).split())))
    return [full for first, full in joined if tid in first]


def _parse_iso(s: str):
    try:
        from datetime import datetime
        return datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def _run_times(manifest: dict, records: list[dict]):
    start = _parse_iso(manifest.get("start_local") or "")
    end = None
    for r in records:
        ts = r.get("timestamps") or {}
        t = _parse_iso(ts.get("local") or "")
        if t is not None and (end is None or t > end):
            end = t
    return start, end


def _load_gv_records(run_dir: str) -> list[dict]:
    gv_dir = run_dir.rstrip(os.sep) + "_gv"
    if not os.path.isdir(gv_dir):
        return []
    try:
        return _report.load_records(gv_dir)
    except OSError:
        return []


def _gv_home07_summary(gv_records: list[dict]) -> dict | None:
    recs = [r for r in gv_records
            if _report.test_of(r) == "HOME-07"
            and _report.model_of(r) == "granite3.2-vision:2b"]
    if not recs:
        return None
    return _report.summarize_group(recs)


def _header_lines(run_id: str, manifest: dict, records: list[dict],
                  gv_records: list[dict]) -> list[str]:
    ov = _report.run_overview(records)
    start, end = _run_times(manifest, records)
    lines = [f"- run_id: {manifest.get('run_id', run_id)}",
             f"- початок (local): {manifest.get('start_local', NO_DATA)}",
             f"- кінець (local): {end.isoformat() if end is not None else NO_DATA}",
             f"- записів: {len(records)}",
             f"- моделей: {ov['n_models']}; тестів: {ov['n_tests']}"]
    lines.append("- за статусами:")
    for st in sorted(ov["counts"]):
        lines.append(f"  - {st}: {ov['counts'][st]}")
    nbrs = [r for r in records
            if _report.verdict_of(r).get("status") == "NOT_RUN_BUDGET"]
    if nbrs:
        pairs: dict[tuple[str, str], int] = Counter()
        for r in nbrs:
            pairs[(_report.model_of(r), _report.test_of(r))] += 1
        pair_txt = "; ".join(
            f"{m} x {t} ({n})" for (m, t), n in sorted(pairs.items()))
        lines.append(f"- покриття неповне: NOT_RUN_BUDGET записів: {len(nbrs)}; "
                     f"пари модель x тест: {pair_txt}.")
    else:
        lines.append("- покриття: повне (без NOT_RUN_BUDGET).")
    if gv_records:
        gv_scored = [r for r in gv_records
                     if _report.verdict_of(r).get("status") in _report.SCORED]
        lines.append(f"- додатковий прогін {manifest.get('run_id', run_id)}_gv "
                     f"(plain-answer адаптер granite3.2-vision:2b / HOME-07): "
                     f"{len(gv_records)} {_plural_zapys(len(gv_records))}, "
                     f"з них оцінених: {len(gv_scored)}; "
                     "ці дві умови (уніфікований JSON-контракт і адаптер) "
                     "не порівнюються напряму як один Q_sem.")
    return lines


def _model_desc_lines(tag: str, recs: list[dict], home_tid: str,
                      per_model: dict) -> list[str]:
    scored = [r for r in recs
              if _report.verdict_of(r).get("status") in _report.SCORED]
    n_ok = sum(1 for r in scored
               if _report.verdict_of(r).get("status") == "OK")
    out = []
    if not scored:
        labels = Counter(_status_label(_report.verdict_of(r)) for r in recs)
        lab_txt = "; ".join(f"{k} (x{n})"
                            for k, n in sorted(labels.items())) or NO_DATA
        out.append(f"Оцінених записів немає (усього записів: {len(recs)}: "
                   f"{lab_txt}).")
        return out
    pct = 100.0 * n_ok / len(scored)
    out.append(f"Оцінено {len(scored)} {_plural_zapys(len(scored))}, "
               f"OK: {n_ok} ({pct:.1f}%).")
    home_s = (per_model.get(tag) or {}).get("tests", {}).get(home_tid)
    if not home_tid:
        out.append("Власний HOME-тест невідомий (мапінг недоступний).")
    elif home_s is None:
        out.append(f"Власний тест {home_tid}: записів немає.")
    elif (home_s.get("n_scored") or 0) == 0:
        counts = home_s.get("counts") or {}
        lab = "; ".join(f"{k} (x{n})" for k, n in sorted(counts.items()))
        out.append(f"Власний тест {home_tid}: не оцінено "
                   f"(n={home_s['n_scored']}/{home_s['n_total']}: {lab}).")
    else:
        out.append(f"Власний тест {home_tid}: Q_sem={home_s['q_sem']:.3f}, "
                   f"Q_strict={home_s['q_strict']:.3f} "
                   f"(n={home_s['n_scored']}/{home_s['n_total']}).")
    fails = [_status_label(_report.verdict_of(r)) for r in scored
             if _report.verdict_of(r).get("status") != "OK"]
    if not fails:
        out.append("Усі оцінені записи — OK.")
    else:
        top = Counter(fails).most_common(2)
        pat = "; ".join(f"{k} — {n} з {len(scored)} оцінених"
                        for k, n in top)
        out.append(f"Помітні патерни: {pat}.")
    return out


def _model_rec_lines(tag: str, recs: list[dict], home_tid: str,
                     per_model: dict, perf_by_tag: dict) -> list[str]:
    scored = [r for r in recs
              if _report.verdict_of(r).get("status") in _report.SCORED]
    if len(scored) < MIN_SCORED_FOR_REC:
        return [f"{INSUFFICIENT}: лише {len(scored)} оцінених записів "
                f"(потрібно щонайменше {MIN_SCORED_FOR_REC}); "
                "рекомендацію не сформульовано, щоб не екстраполювати."]
    tests = {t: s for t, s in
             (per_model.get(tag) or {}).get("tests", {}).items() if t != "PERF"}
    scored_tests = {t: s for t, s in tests.items()
                    if (s.get("n_scored") or 0) > 0}
    if not scored_tests:
        return [f"{INSUFFICIENT}: жоден тест не має оцінених записів."]
    best_tid = sorted(scored_tests,
                      key=lambda t: (-scored_tests[t]["q_sem"],
                                     -scored_tests[t]["n_scored"], t))[0]
    worst_tid = sorted(scored_tests,
                       key=lambda t: (scored_tests[t]["q_sem"],
                                      -scored_tests[t]["n_scored"], t))[0]
    b, w = scored_tests[best_tid], scored_tests[worst_tid]
    if best_tid == worst_tid:
        s1 = (f"Єдиний оцінений тест — {best_tid} (Q_sem={b['q_sem']:.3f}, "
              f"n={b['n_scored']}/{b['n_total']}).")
    else:
        s1 = (f"Найкращий результат — {best_tid} (Q_sem={b['q_sem']:.3f}, "
              f"n={b['n_scored']}/{b['n_total']}); "
              f"найгірший — {worst_tid} (Q_sem={w['q_sem']:.3f}, "
              f"n={w['n_scored']}/{w['n_total']}).")
    perf = perf_by_tag.get(tag) or {}
    try:
        gen = float(perf.get("gen_tok_s", ""))
        s2 = f"Швидкість генерації за perf.csv: {gen:.1f} ток/с."
    except (TypeError, ValueError):
        s2 = "Швидкості в perf.csv для цієї моделі немає."
    zero_tests = sorted(t for t, s in scored_tests.items()
                        if s["q_sem"] == 0.0)
    if zero_tests:
        parts = []
        for t in zero_tests:
            own = scored_tests[t]
            n_txt = f"{own['n_scored']}/{own['n_total']}"
            best_all: float | None = None
            for m, ms in per_model.items():
                row = (ms.get("tests") or {}).get(t)
                if row is not None and (row.get("n_scored") or 0) > 0:
                    q = float(row["q_sem"])
                    best_all = q if best_all is None else max(best_all, q)
            if best_all is not None and best_all <= 0.10:
                parts.append(
                    f"{t} (Q_sem=0.000, n={n_txt} — тест майже не "
                    "розв'язаний жодною моделлю)")
            else:
                parts.append(f"{t} (Q_sem=0.000)")
        s3 = f"Варто уникати: {', '.join(parts)}."
    else:
        fails = Counter(_status_label(_report.verdict_of(r)) for r in scored
                        if _report.verdict_of(r).get("status") != "OK")
        if fails:
            k, n = fails.most_common(1)[0]
            s3 = (f"Обережно із задачами, де повторюється {k} (x{n}): "
                  "це найчастіша невдача моделі.")
        else:
            s3 = "Невдач серед оцінених записів немає."
    void_home = (home_tid and best_tid == home_tid and
                 b["q_sem"] > 0.0 and w["q_sem"] == 0.0 and worst_tid != home_tid)
    if void_home:
        s3 += (f" Власний тест {home_tid} складено, тож модель придатна "
               "насамперед для задач свого профілю.")
    return [s1, s2, s3]


def _model_quote_lines(tag: str, recs: list[dict]) -> list[str] | None:
    bad = sorted(
        (r for r in recs
         if _report.verdict_of(r).get("status") in _report.SCORED
         and _report.verdict_of(r).get("status") != "OK"
         and _content_of(r).strip()),
        key=lambda r: r.get("key", ""))
    if not bad:
        non_empty = any(
            _report.verdict_of(r).get("status") in _report.SCORED
            and _report.verdict_of(r).get("status") != "OK" for r in recs)
        if not non_empty:
            return None
        return ["текстового вмісту відповідей у невдалих записах немає "
                "(порожній response.content) — цитату навести неможливо; "
                "деталі див. у results.jsonl за полем verdict.details."]
    lines = []
    for r in bad[:2]:
        v = _report.verdict_of(r)
        quote, cut = _shorten(_content_of(r).strip())
        label = (f"{_report.test_of(r)} / {_case_of(r)} / "
                 f"{v.get('status')}[{_sub_reason(v)}]")
        lines.append(f"- {label}: «{quote}»")
        if cut:
            lines[-1] += f" (уривок скорочено: показано перші {QUOTE_LIMIT} символів)"
    return lines


def _per_model_lines(records: list[dict], per_model: dict,
                     home_of_model: dict, perf_by_tag: dict,
                     gv_summary: dict | None) -> list[str]:
    lines: list[str] = []
    tags = sorted({ _report.model_of(r) for r in records
                   if _report.model_of(r) != "unknown"})
    if not tags:
        return [NO_DATA]
    by_tag: dict[str, list[dict]] = {}
    for r in records:
        by_tag.setdefault(_report.model_of(r), []).append(r)
    for tag in tags:
        recs = by_tag[tag]
        home_tid = home_of_model.get(tag, "")
        lines.append(f"### {tag}")
        lines.append("")
        desc = _model_desc_lines(tag, recs, home_tid, per_model)
        for i, s in enumerate(desc):
            lines.append(f"**Опис поведінки.** {s}" if i == 0 else s)
        lines.append("")
        for i, s in enumerate(_model_rec_lines(tag, recs, home_tid,
                                               per_model, perf_by_tag)):
            lines.append(f"**Рекомендація.** {s}" if i == 0 else s)
        lines.append("")
        if (tag == "granite3.2-vision:2b" and gv_summary is not None
                and (gv_summary.get("n_total") or 0) > 0):
            main_s = (per_model.get(tag) or {}).get("tests", {}).get("HOME-07")
            if main_s is not None and (main_s.get("n_scored") or 0) > 0:
                lines.append(
                    f"**HOME-07 окремо.** Під уніфікованим JSON-контрактом: "
                    f"Q_sem={main_s['q_sem']:.3f} "
                    f"(n={main_s['n_scored']}/{main_s['n_total']}); під "
                    "документованим plain-answer адаптером "
                    f"(додатковий прогін _gv): Q_sem={gv_summary['q_sem']:.3f} "
                    f"(n={gv_summary['n_scored']}/{gv_summary['n_total']}). "
                    "Ці два числа отримано за різних умов і не порівнюються "
                    "напряму як один Q_sem.")
            else:
                lines.append(
                    "**HOME-07 окремо.** В основному прогоні оцінених записів "
                    "немає; під документованим plain-answer адаптером "
                    f"(додатковий прогін _gv): Q_sem={gv_summary['q_sem']:.3f} "
                    f"(n={gv_summary['n_scored']}/{gv_summary['n_total']}).")
            lines.append("")
        quotes = _model_quote_lines(tag, recs)
        if quotes is not None:
            lines.append("**Приклади помилок.**")
            lines.extend(quotes)
            lines.append("")
    return lines


def _per_test_lines(records: list[dict], per_test: dict,
                    gv_summary: dict | None) -> list[str]:
    lines: list[str] = []
    tids = sorted(t for t in per_test if t != "PERF")
    if not tids:
        return [NO_DATA]
    by_test: dict[str, list[dict]] = {}
    for r in records:
        by_test.setdefault(_report.test_of(r), []).append(r)
    for tid in tids:
        rows = per_test[tid]
        scored_rows = [r for r in rows if (r.get("n_scored") or 0) > 0]
        lines.append(f"### {tid}")
        lines.append("")
        if not scored_rows:
            counts: dict[str, int] = {}
            for r in rows:
                for st, n in (r.get("counts") or {}).items():
                    counts[st] = counts.get(st, 0) + n
            lab = "; ".join(f"{k} (x{n})" for k, n in sorted(counts.items()))
            lines.append(f"Оцінених моделей немає ({lab or NO_DATA}).")
            lines.append("")
            continue
        qs = [(r["model"], r["q_sem"]) for r in scored_rows]
        qmin = min(q for _, q in qs)
        qmax = max(q for _, q in qs)
        best = sorted(scored_rows,
                      key=lambda r: (-r["q_sem"], -r["n_scored"], r["model"]))[0]
        worst = sorted(scored_rows,
                       key=lambda r: (r["q_sem"], -r["n_scored"], r["model"]))[0]
        n_recs = sum(r["n_scored"] for r in scored_rows)
        if len(scored_rows) == 1:
            only = scored_rows[0]
            lines.append(
                f"Оцінено моделей: 1 (оцінених записів: {n_recs}); "
                f"єдиний оцінений — {only['model']} "
                f"(Q_sem={only['q_sem']:.3f}, "
                f"n={only['n_scored']}/{only['n_total']}).")
        else:
            lines.append(
                f"Оцінено моделей: {len(scored_rows)} "
                f"(оцінених записів: {n_recs}); Q_sem від {qmin:.3f} "
                     f"({worst['model']}) до {qmax:.3f} ({best['model']}); "
                     f"найкраще — {best['model']} "
                     f"(Q_sem={best['q_sem']:.3f}, "
                     f"n={best['n_scored']}/{best['n_total']}), "
                     f"найгірше — {worst['model']} "
                     f"(Q_sem={worst['q_sem']:.3f}, "
                     f"n={worst['n_scored']}/{worst['n_total']}).")
        fails = Counter()
        for r in by_test.get(tid, []):
            v = _report.verdict_of(r)
            if (v.get("status") in _report.SCORED
                    and v.get("status") != "OK"):
                fails[_status_label(v)] += 1
        if fails:
            k, n = fails.most_common(1)[0]
            lines.append(f"Найчастіша причина невдачі: {k} — {n} {_plural_raz(n)}.")
        else:
            lines.append("Невдач немає (усі оцінені записи — OK).")
        if tid == "HOME-07" and gv_summary is not None:
            lines.append(
                "Під уніфікованим JSON-контрактом (цей прогін) — див. рядки "
                "вище; під документованим plain-answer адаптером (додатковий "
                f"прогін _gv, granite3.2-vision:2b): "
                f"Q_sem={gv_summary['q_sem']:.3f} "
                f"(n={gv_summary['n_scored']}/{gv_summary['n_total']}). "
                "Ці два числа отримано за різних умов і не порівнюються "
                "напряму як один Q_sem.")
        for note in _plan_notes_for_test(tid):
            lines.append(f"Контекст з MASTER_PLAN (розд. 4/5): {note[2:]}")
        lines.append("")
    return lines


def _perf_lines(perf_csv_rows: list[dict]) -> list[str]:
    if not perf_csv_rows:
        return [NO_DATA]

    def _num(r: dict, k: str):
        try:
            return float(r.get(k, ""))
        except (TypeError, ValueError):
            return None

    rows = sorted(perf_csv_rows,
                  key=lambda r: (_num(r, "gen_tok_s") is None,
                                 -(_num(r, "gen_tok_s") or 0.0),
                                 str(r.get("tag", ""))))

    def _fmt(v, nd=3):
        try:
            if v is None or (isinstance(v, str) and not v.strip()):
                return NO_DATA
            return f"{float(v):.{nd}f}"
        except (TypeError, ValueError):
            return NO_DATA

    lines = ["| Модель | cold load, s | TTFT, s | prompt tok/s | gen tok/s | "
             "offload ratio |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r.get('tag', '?')} | {_fmt(r.get('cold_load_s'))} | "
                     f"{_fmt(r.get('ttft_s'))} | "
                     f"{_fmt(r.get('prompt_tok_s'), 1)} | "
                     f"{_fmt(r.get('gen_tok_s'), 1)} | "
                     f"{_fmt(r.get('offload_ratio'))} |")
    partial = sorted(str(r.get("tag", "")) for r in rows
                     if _num(r, "offload_ratio") is not None
                     and _num(r, "offload_ratio") < 1.0)
    if partial:
        lines.append("- Частковий CPU offload (offload ratio < 1.0; модель не "
                     "вмістилась у 8 GB VRAM, тому повільніша за свій розмір): "
                     + ", ".join(partial) + ".")
    else:
        lines.append("- Жодна модель з виміряним offload ratio не працювала з "
                     "частковим CPU offload (усі мають offload ratio 1.0 або "
                     "вимір відсутній).")
    return lines


def build_markdown(run_id: str, manifest: dict, records: list[dict],
                   perf_csv_rows: list[dict],
                   gv_records: list[dict]) -> str:
    per_test, per_model, _ = _report.compute_tables(records)
    _, home_of_model = _home_maps()
    gv_summary = _gv_home07_summary(gv_records) if gv_records else None
    perf_by_tag = {str(r.get("tag", "")): r for r in perf_csv_rows}
    parts = [f"# АНАЛІЗ ПРОГОНУ — {manifest.get('run_id', run_id)}", ""]
    parts.append("## 1. Огляд прогону")
    parts.extend(_header_lines(manifest.get("run_id", run_id),
                               manifest, records, gv_records))
    parts.append("")
    parts.append("## 2. Моделі")
    parts.extend(_per_model_lines(records, per_model, home_of_model,
                                  perf_by_tag, gv_summary))
    parts.append("## 3. Тести")
    parts.extend(_per_test_lines(records, per_test, gv_summary))
    parts.append("## 4. Швидкість на цьому ПК")
    parts.extend(_perf_lines(perf_csv_rows))
    parts.append("")
    return "\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Analysis report (UK) for a run")
    p.add_argument("run_id", help="run id or path to run dir")
    p.add_argument("--results-root", default=None)
    a = p.parse_args(argv)
    run_dir = _resolve_run_dir(a.run_id, a.results_root)
    os.makedirs(run_dir, exist_ok=True)
    manifest = _load_manifest(run_dir)
    records = _report.load_records(run_dir)
    perf_csv_rows = _load_perf(run_dir)
    gv_records = _load_gv_records(run_dir)
    md = build_markdown(os.path.basename(run_dir), manifest, records,
                        perf_csv_rows, gv_records)
    with open(os.path.join(run_dir, MD_NAME), "w", encoding="utf-8") as f:
        f.write(md)
    print(f"analysis written to {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
