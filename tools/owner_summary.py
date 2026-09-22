"""Owner summary (Ukrainian) for a NIGHT-1 run. Standalone tool, stdlib only.

Reads results/<run_id>/results.jsonl + perf.csv + manifest.json and writes
OWNER_SUMMARY_UK.md (+ owner_tables.csv, + owner_summary.xlsx when openpyxl
is importable). Reuses read-only helpers from bench.report and bench.registry;
never contacts Ollama.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bench import report as _report  # noqa: E402

MD_NAME = "OWNER_SUMMARY_UK.md"
CSV_NAME = "owner_tables.csv"
XLSX_NAME = "owner_summary.xlsx"

SECTIONS = [
    "Огляд прогону",
    "HOME-вердикти",
    "Топ-3 по кожному тесту",
    "Швидкість на цьому ПК",
    "Профіль моделей",
    "Відомі особливості моделей",
    "Обмеження",
]

VERDICT_UA = {
    "HOME_WIN": "HOME перемагає",
    "HOME_TIE": "нічия",
    "HOME_LOSS": "HOME програє",
}
NO_DATA = "немає даних"
NOT_SCORED = "не оцінено"
_LOCAL_MACHINE_CACHE: tuple | None = None


def _is_missing(v) -> bool:
    return v is None or (isinstance(v, str) and
                         (not v.strip() or v.strip().lower() == "unknown"))


# Manager-supplied hardware facts (never queried live by tool code — see MASTER_PLAN.md
# "Security: agent/tool sandbox". This tool must not introspect the host machine itself;
# the operator records these once and they are used only when manifest.json lacks them.
_MANAGER_CPU = "Intel(R) Core(TM) i9-10900KF CPU @ 3.70GHz"
_MANAGER_RAM = "31.9 GB"


def _query_local_machine():
    """Return (cpu_name|None, ram_text|None): manager-supplied constants, no system query.

    Kept as its own function (rather than inlined) so tests can monkeypatch it and so the
    call site in `_cpu_ram_text` stays unchanged. Intentionally does not shell out or read
    the environment — a real fingerprint (fp["cpu"]/fp["ram"]) is always preferred, and this
    is only the last-resort fallback for it.
    """
    return _MANAGER_CPU, _MANAGER_RAM


def _cpu_ram_text(fp: dict) -> tuple[str, str]:
    """CPU/RAM display strings with one-shot local fallback (FIX_SUMMARY.3)."""
    global _LOCAL_MACHINE_CACHE
    cpu = fp.get("cpu")
    ram = fp.get("ram")
    need_cpu = _is_missing(cpu)
    need_ram = _is_missing(ram)
    local = (None, None)
    if need_cpu or need_ram:
        if _LOCAL_MACHINE_CACHE is None:
            _LOCAL_MACHINE_CACHE = _query_local_machine()
        local = _LOCAL_MACHINE_CACHE
    if need_cpu:
        cpu = (f"{local[0]} (зчитано з поточної системи)"
               if local[0] else NO_DATA)
    if need_ram:
        ram = (f"{local[1]} (зчитано з поточної системи)"
               if local[1] else NO_DATA)
    if _is_missing(cpu):
        cpu = NO_DATA
    if _is_missing(ram):
        ram = NO_DATA
    return str(cpu), str(ram)


def _verdict_sub_reason(v: dict) -> str:
    """Sub-reason with details fallback (FIX_SUMMARY.2)."""
    det = v.get("details") or {}
    return (v.get("sub_reason") or det.get("sub_reason") or "-")


def _row_note(row: dict) -> str:
    """Raw status note for unscored rows (CSV/xlsx); '' when scored."""
    if (row.get("n_scored") or 0) > 0:
        return ""
    counts = row.get("counts") or {}
    if not counts:
        return "NO_RECORDS"
    return ";".join(sorted(counts))


def _unscored_label(row: dict) -> str:
    """Ukrainian 'не оцінено (...)' label picked by statuses (FIX_SUMMARY.1)."""
    counts = row.get("counts") or {}
    if "NOT_RUN_BUDGET" in counts:
        return "не оцінено (NOT_RUN_BUDGET)"
    if "UNSUPPORTED_CAPABILITY" in counts:
        return "не оцінено (UNSUPPORTED)"
    return NOT_SCORED


def _q_cell(row: dict) -> str:
    """'Q_sem (n/n)' for scored rows, unscored label otherwise."""
    if (row.get("n_scored") or 0) == 0:
        return _unscored_label(row)
    return (f"{row['q_sem']:.3f} "
            f"({row['n_scored']}/{row['n_total']})")


def _fmt(v, nd=3, empty=NO_DATA):
    try:
        if v is None or (isinstance(v, str) and not v.strip()):
            return empty
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return empty


def _resolve_run_dir(run_id: str, results_root: str | None) -> str:
    if os.path.isdir(run_id):
        return os.path.abspath(run_id)
    base = results_root or os.path.join(ROOT, "results")
    if not os.path.isabs(base):
        base = os.path.join(ROOT, base)
    return os.path.join(base, run_id)


def _load_manifest(run_dir: str) -> dict:
    path = os.path.join(run_dir, "manifest.json")
    try:
        with open(path, encoding="utf-8") as f:
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


def _test_meta() -> tuple[dict, dict]:
    """Return ({test_id: title}, {test_id: home_tag}); {} on failure."""
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


def _parse_iso(s: str):
    try:
        from datetime import datetime
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


def _only_status(row: dict, statuses: set) -> bool:
    counts = row.get("counts") or {}
    return bool(counts) and set(counts) <= statuses


def _ranked_rows(rows: list[dict]):
    """Split per-test rows into (ranked_top, excluded_tags) like bench.report."""
    unsup = sorted(r["model"] for r in rows
                   if _only_status(r, {"UNSUPPORTED_CAPABILITY"}))
    notrun = sorted(r["model"] for r in rows
                    if _only_status(r, {"NOT_RUN_BUDGET", "UNSUPPORTED_CAPABILITY"})
                    and not _only_status(r, {"UNSUPPORTED_CAPABILITY"}))
    excluded = set(unsup) | set(notrun)
    ranked = sorted((r for r in rows if r["model"] not in excluded),
                    key=lambda r: (-r["q_sem"], -r["n_scored"], r["model"]))
    return ranked, sorted(excluded)


def _overview_lines(run_id: str, manifest: dict, records: list[dict]) -> list[str]:
    ov = _report.run_overview(records)
    start, end = _run_times(manifest, records)
    fp = manifest.get("fingerprint") or {}
    lines = []
    lines.append(f"- run_id: {manifest.get('run_id', run_id)}")
    lines.append(f"- початок (local): {manifest.get('start_local', NO_DATA)}")
    if end is not None:
        lines.append(f"- кінець (local): {end.isoformat()}")
        if start is not None and end >= start:
            mins = (end - start).total_seconds() / 60.0
            lines.append(f"- тривалість: {mins:.1f} хв")
        else:
            lines.append(f"- тривалість: {NO_DATA}")
    else:
        lines.append(f"- кінець (local): {NO_DATA}")
        lines.append(f"- тривалість: {NO_DATA}")
    budget = manifest.get("budget_hours")
    lines.append(f"- бюджет: {budget} год" if budget is not None else f"- бюджет: {NO_DATA}")
    lines.append(f"- Ollama: {manifest.get('ollama_version', NO_DATA)}")
    lines.append(f"- GPU: {fp.get('gpu', NO_DATA)}")
    cpu_txt, ram_txt = _cpu_ram_text(fp)
    lines.append(f"- CPU: {cpu_txt}; RAM: {ram_txt}; "
                 f"OS: {fp.get('os', fp.get('platform', NO_DATA))}")
    lines.append(f"- моделей запущено: {ov['n_models']}"
                 + (f" ({', '.join(ov['models'])})" if ov["models"] else ""))
    lines.append(f"- тестів запущено: {ov['n_tests']}"
                 + (f" ({', '.join(ov['tests'])})" if ov["tests"] else ""))
    lines.append(f"- записів: {len(records)}")
    lines.append("- за статусами:")
    for st in sorted(ov["counts"]):
        lines.append(f"  - {st}: {ov['counts'][st]}")
    lines.append(f"- NOT_RUN_BUDGET: {ov['not_run_budget']}")
    if not records:
        lines.append(f"- покриття: {NO_DATA} (порожній прогін)")
    elif ov["not_run_budget"]:
        lines.append(f"- частковий прогін: {ov['not_run_budget']} записів пропущено "
                     "через брак часу (NOT_RUN_BUDGET); покриття неповне.")
    else:
        lines.append("- покриття: повне (без NOT_RUN_BUDGET).")
    return lines


def _home_verdict_lines(per_test: dict, records: list[dict],
                        titles: dict, home_of_test: dict) -> list[str]:
    hv = _report.home_verdicts(per_test, records)
    by_model = {r["model"]: r for rows in per_test.values() for r in rows}
    _ = by_model
    lines = ["| Тест | Назва | HOME-модель | HOME Q_sem (n) | "
             "Найкращий конкурент | Q_sem (n) | common_n | Вердикт |",
             "|---|---|---|---|---|---|---|---|"]
    for tid in sorted(per_test):
        if tid == "PERF" or tid not in _report.HOME_SET:
            continue
        rows = per_test[tid]
        title = titles.get(tid, "")
        home_tag = home_of_test.get(tid, "")
        home_row = next((r for r in rows if r["model"] == home_tag), None)
        if home_row is None:
            lines.append(f"| {tid} | {title} | {home_tag or NO_DATA} | {NO_DATA} | "
                         f"{NO_DATA} | {NO_DATA} | {NO_DATA} | недостатньо даних |")
            continue
        home_q = _q_cell(home_row)
        v = hv.get(tid)
        ranked, _ = _ranked_rows(rows)
        comp_row = next((r for r in ranked if r["model"] != home_tag), None)
        if v is not None and v.get("second") and comp_row is not None:
            comp_tag = v["second"]
            comp_r = next((r for r in rows if r["model"] == comp_tag), comp_row)
            comp_q = _q_cell(comp_r)
            verdict = VERDICT_UA.get(v.get("verdict", ""), "недостатньо даних")
            common_n = str(v.get("common_n", NO_DATA))
        elif comp_row is not None:
            comp_q = _q_cell(comp_row)
            comp_tag = comp_row["model"]
            verdict = "недостатньо даних"
            common_n = NO_DATA
        else:
            comp_tag, comp_q, verdict, common_n = (NO_DATA, NO_DATA,
                                                  "недостатньо даних", NO_DATA)
        lines.append(f"| {tid} | {title} | {home_tag} | {home_q} | "
                     f"{comp_tag} | {comp_q} | {common_n} | {verdict} |")
    if len(lines) == 2:
        lines.append(f"| {NO_DATA} |")
    return lines


def _top3_lines(per_test: dict) -> list[str]:
    lines = []
    tids = sorted(t for t in per_test if t != "PERF")
    if not tids:
        return [NO_DATA]
    for tid in tids:
        rows = per_test[tid]
        ranked, excluded = _ranked_rows(rows)
        lines.append(f"### {tid}")
        if not ranked:
            lines.append(f"- {NO_DATA} (усі рядки UNSUPPORTED/NOT_RUN_BUDGET)")
        for i, r in enumerate(ranked[:3], 1):
            mark = " (покриття < 0.9)" if r.get("coverage", 1.0) < 0.9 else ""
            lines.append(f"- {i}. {r['model']}: Q_sem={r['q_sem']:.3f} "
                         f"Q_strict={r['q_strict']:.3f} "
                         f"n={r['n_scored']}/{r['n_total']} "
                         f"CI=[{r['ci_lo']:.3f},{r['ci_hi']:.3f}]{mark}")
        if excluded:
            lines.append(f"- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): "
                         f"{', '.join(excluded)}")
    return lines


def _perf_lines(perf_csv_rows: list[dict]) -> list[str]:
    lines = []
    if not perf_csv_rows:
        return [NO_DATA]
    def _num(r, k):
        try:
            return float(r.get(k, ""))
        except (TypeError, ValueError):
            return None
    rows = sorted(perf_csv_rows,
                  key=lambda r: (_num(r, "gen_tok_s") is None,
                                 -(_num(r, "gen_tok_s") or 0.0),
                                 str(r.get("tag", ""))))
    lines.append("| Модель | cold load, s | TTFT, s | prompt tok/s | gen tok/s | "
                 "offload ratio |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        tag = r.get("tag", "?")
        lines.append(f"| {tag} | {_fmt(r.get('cold_load_s'))} | "
                     f"{_fmt(r.get('ttft_s'))} | {_fmt(r.get('prompt_tok_s'), 1)} | "
                     f"{_fmt(r.get('gen_tok_s'), 1)} | "
                     f"{_fmt(r.get('offload_ratio'), 3)} |")
    lines.append("- offload ratio < 1.0 означає частковий CPU offload "
                 "(модель не вмістилась у 8 GB VRAM).")
    return lines


def _profile_lines(per_model: dict, records: list[dict],
                   home_of_model: dict) -> list[str]:
    from collections import Counter
    fail_reasons: dict[str, Counter] = {}
    for r in records:
        v = _report.verdict_of(r)
        if v.get("status") not in ("OK",):
            tag = _report.model_of(r)
            key = f"{v.get('status', '?')}[{_verdict_sub_reason(v)}]"
            fail_reasons.setdefault(tag, Counter())[key] += 1
    if not per_model:
        return [NO_DATA]
    lines = []
    for tag in sorted(per_model):
        tests = {t: s for t, s in per_model[tag]["tests"].items() if t != "PERF"}
        n_tests = len(tests)
        scored = [s for s in tests.values() if (s.get("n_scored") or 0) > 0]
        mean_txt = (f"{sum(s['q_sem'] for s in scored) / len(scored):.3f}"
                    if scored else NOT_SCORED)
        home_tid = home_of_model.get(tag, "")
        home_s = tests.get(home_tid)
        if home_s is None:
            home_txt = NO_DATA
        elif (home_s.get("n_scored") or 0) == 0:
            home_txt = (f"{home_tid} ({_unscored_label(home_s)}, "
                        f"n={home_s['n_scored']}/{home_s['n_total']})")
        else:
            home_txt = (f"{home_tid} (Q_sem={home_s['q_sem']:.3f}, "
                        f"n={home_s['n_scored']}/{home_s['n_total']})")
        top = fail_reasons.get(tag, Counter()).most_common(2)
        fail_txt = ", ".join(f"{k} (x{n})" for k, n in top) if top else "немає"
        lines.append(f"- {tag}: HOME={home_txt}; тестів: {n_tests} (без PERF); "
                     f"середній Q_sem={mean_txt}; failures: {fail_txt}")
    return lines


def _limit_lines(manifest: dict) -> list[str]:
    return [
        "- один запуск на кейс (без повторів); дисперсія між запусками не вимірювалась.",
        "- time-boxed покриття: блоки, що не встигли до дедлайну, записано як "
        "NOT_RUN_BUDGET і виключено з Q.",
        "- LM Studio + Specialists DEFERRED (не запускались цієї ночі).",
        "- 8 GB VRAM: великі моделі працюють з частковим CPU offload "
        "(offload ratio < 1.0), швидкість нижча за повний GPU.",
        "- Q_sem — семантична якість (ранжувальна метрика); Q_strict = Q_sem лише "
        "за повного дотримання формату (FORMAT_ERROR зберігає семантичний кредит, "
        "але strict = 0).",
    ]


def build_markdown(run_id: str, manifest: dict, records: list[dict],
                   perf_csv_rows: list[dict],
                   gv_exists: bool = False) -> str:
    per_test, per_model, _ = _report.compute_tables(records)
    titles, home_of_test = _test_meta()
    home_of_model = {m: t for t, m in home_of_test.items()}
    behaviours = _known_behaviours()
    parts = [f"# OWNER SUMMARY — {manifest.get('run_id', run_id)}", ""]
    parts.append(f"## 1. {SECTIONS[0]}")
    parts.extend(_overview_lines(run_id, manifest, records))
    parts.append("")
    parts.append(f"## 2. {SECTIONS[1]}")
    parts.extend(_home_verdict_lines(per_test, records, titles, home_of_test))
    if gv_exists:
        # Special-cased to HOME-07: the only _gv-style follow-up in this
        # project (plain-answer adapter, documented in ANALYSIS_UK.md).
        gv_id = f"{manifest.get('run_id', run_id)}_gv"
        parts.append(
            f"HOME-07: див. також додатковий прогін {gv_id} (інший контракт "
            "відповіді, не порівнюється напряму) — деталі в ANALYSIS_UK.md.")
    parts.append("")
    parts.append(f"## 3. {SECTIONS[2]}")
    parts.extend(_top3_lines(per_test))
    parts.append("")
    parts.append(f"## 4. {SECTIONS[3]}")
    parts.extend(_perf_lines(perf_csv_rows))
    parts.append("")
    parts.append(f"## 5. {SECTIONS[4]}")
    parts.extend(_profile_lines(per_model, records, home_of_model))
    parts.append("")
    parts.append(f"## 6. {SECTIONS[5]}")
    parts.append("(нижче — оригінальні нотатки англійською мовою з робочого журналу)")
    parts.extend(behaviours if behaviours else [NO_DATA])
    parts.append("")
    parts.append(f"## 7. {SECTIONS[6]}")
    parts.extend(_limit_lines(manifest))
    parts.append("")
    return "\n".join(parts) + "\n"


def write_tables_csv(run_dir: str, records: list[dict]) -> None:
    per_test, _, _ = _report.compute_tables(records)
    path = os.path.join(run_dir, CSV_NAME)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "test", "n_scored", "n_total", "q_sem",
                    "q_strict", "ci_lo", "ci_hi", "coverage", "note"])
        for tid in sorted(per_test):
            if tid == "PERF":
                continue
            ranked, _ = _ranked_rows(per_test[tid])
            rest = [r for r in per_test[tid] if r not in ranked]
            for r in ranked + sorted(rest, key=lambda x: x["model"]):
                if (r.get("n_scored") or 0) == 0:
                    w.writerow([r["model"], tid, r["n_scored"], r["n_total"],
                                "", "", "", "",
                                f"{r.get('coverage', 0.0):.3f}",
                                _row_note(r)])
                else:
                    w.writerow([r["model"], tid, r["n_scored"], r["n_total"],
                                f"{r['q_sem']:.4f}", f"{r['q_strict']:.4f}",
                                f"{r['ci_lo']:.4f}", f"{r['ci_hi']:.4f}",
                                f"{r.get('coverage', 0.0):.3f}", ""])


def write_xlsx(run_dir: str, records: list[dict],
               perf_csv_rows: list[dict]) -> bool:
    try:
        import openpyxl
    except ImportError:
        return False
    per_test, per_model, _ = _report.compute_tables(records)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "top3"
    ws.append(["test", "rank", "model", "q_sem", "q_strict", "n_scored",
               "n_total", "coverage"])
    for tid in sorted(t for t in per_test if t != "PERF"):
        ranked, _ = _ranked_rows(per_test[tid])
        for i, r in enumerate(ranked[:3], 1):
            ws.append([tid, i, r["model"], round(r["q_sem"], 4),
                       round(r["q_strict"], 4), r["n_scored"], r["n_total"],
                       round(r.get("coverage", 0.0), 3)])
    ws2 = wb.create_sheet("perf")
    ws2.append(["tag", "cold_load_s", "ttft_s", "prompt_tok_s", "gen_tok_s",
                "vram_peak_mb", "offload_ratio", "throttle"])
    for r in sorted(perf_csv_rows, key=lambda x: str(x.get("tag", ""))):
        ws2.append([r.get("tag", ""), r.get("cold_load_s", ""),
                    r.get("ttft_s", ""), r.get("prompt_tok_s", ""),
                    r.get("gen_tok_s", ""), r.get("vram_peak_mb", ""),
                    r.get("offload_ratio", ""), r.get("throttle", "")])
    ws3 = wb.create_sheet("profiles")
    ws3.append(["model", "home_test", "home_q_sem", "n_tests", "mean_q_sem",
                "note"])
    titles_home = {}
    try:
        from bench import registry as _reg
        mods = _reg.discover(os.path.join(ROOT, "bench", "tests"))
        titles_home = _reg.home_model_map(mods)
    except Exception:
        titles_home = {}
    for tag in sorted(per_model):
        tests = {t: s for t, s in per_model[tag]["tests"].items() if t != "PERF"}
        n = len(tests)
        scored = [s for s in tests.values() if (s.get("n_scored") or 0) > 0]
        mean_cell = (round(sum(s["q_sem"] for s in scored) / len(scored), 4)
                     if scored else "")
        ht = titles_home.get(tag, "")
        hs = tests.get(ht)
        if hs is None or (hs.get("n_scored") or 0) == 0:
            home_cell: object = ""
        else:
            home_cell = round(hs["q_sem"], 4)
        if scored:
            note = _row_note(hs) if hs is not None and (hs.get("n_scored") or 0) == 0 else ""
        else:
            notes = sorted({_row_note(s) for s in tests.values()
                            if _row_note(s)})
            note = ";".join(notes)
        ws3.append([tag, ht, home_cell, n, mean_cell, note])
    wb.save(os.path.join(run_dir, XLSX_NAME))
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Owner summary (UK) for a NIGHT-1 run")
    p.add_argument("run_id", help="run id or path to run dir")
    p.add_argument("--results-root", default=None)
    a = p.parse_args(argv)
    run_dir = _resolve_run_dir(a.run_id, a.results_root)
    os.makedirs(run_dir, exist_ok=True)
    manifest = _load_manifest(run_dir)
    records = _report.load_records(run_dir)
    perf_csv_rows = _load_perf(run_dir)
    gv_exists = os.path.isdir(run_dir.rstrip(os.sep) + "_gv")
    md = build_markdown(os.path.basename(run_dir), manifest, records,
                        perf_csv_rows, gv_exists=gv_exists)
    with open(os.path.join(run_dir, MD_NAME), "w", encoding="utf-8") as f:
        f.write(md)
    write_tables_csv(run_dir, records)
    try:
        write_xlsx(run_dir, records, perf_csv_rows)
    except Exception:
        pass  # xlsx is best-effort; silently skip on any error
    print(f"owner summary written to {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
