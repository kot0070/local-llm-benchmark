"""NIGHT-1 report: summary.md, per-model reports, CSVs, bootstrap CIs."""
from __future__ import annotations

import csv
import json
import math
import os
import random
import statistics

SCORED = {"OK", "WRONG_ANSWER", "FORMAT_ERROR", "EMPTY_OUTPUT", "OUTPUT_TRUNCATED"}
HOME_SET = {f"HOME-{i:02d}" for i in range(1, 25)}


def load_records(run_dir: str) -> list[dict]:
    path = os.path.join(run_dir, "results.jsonl")
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    # --resume appends re-runs of non-final keys: keep only the last record per key
    last = {}
    for i, r in enumerate(out):
        k = r.get("key")
        if k:
            last[k] = i
    return [r for i, r in enumerate(out) if not r.get("key") or last[r["key"]] == i]


def test_of(rec: dict) -> str:
    key = rec.get("key", "")
    parts = key.split("|")
    if len(parts) >= 4:
        return parts[3].split("@")[0]
    return rec.get("test_id", "PERF")


def model_of(rec: dict) -> str:
    ident = rec.get("identity") or {}
    if ident.get("tag"):
        return ident["tag"]
    key = rec.get("key", "")
    parts = key.split("|")
    if len(parts) >= 3:
        return parts[2].split("@")[0]
    return "unknown"


def verdict_of(rec: dict) -> dict:
    return rec.get("verdict") or {}


def sem_of(rec: dict) -> float:
    try:
        return float(verdict_of(rec).get("sem", 0.0))
    except (TypeError, ValueError):
        return 0.0


def strict_of(rec: dict) -> float:
    try:
        return float(verdict_of(rec).get("strict", 0.0))
    except (TypeError, ValueError):
        return 0.0


def wall_of(rec: dict) -> float | None:
    try:
        t = (rec.get("timing") or {})
        v = t.get("wall_s")
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def bootstrap_ci(vals: list[float], b: int = 1000, seed: int = 0) -> tuple[float, float]:
    if not vals:
        return (0.0, 0.0)
    if len(vals) == 1:
        return (vals[0], vals[0])
    rng = random.Random(seed)
    n = len(vals)
    means = []
    for _ in range(b):
        s = sum(vals[rng.randrange(n)] for _ in range(n)) / n
        means.append(s)
    means.sort()
    lo = means[int(0.025 * b)]
    hi = means[int(0.975 * b) - 1]
    return (lo, hi)


def paired_diff_ci(a: list[float], c: list[float], b: int = 1000,
                   seed: int = 0) -> tuple[float, float, float]:
    """Bootstrap CI of mean(a - c) on the common case set."""
    diffs = [x - y for x, y in zip(a, c)]
    mean = sum(diffs) / len(diffs) if diffs else 0.0
    lo, hi = bootstrap_ci(diffs, b, seed)
    return (mean, lo, hi)


def summarize_group(recs: list[dict]) -> dict:
    scored = [r for r in recs if verdict_of(r).get("status") in SCORED]
    sems = [sem_of(r) for r in scored]
    stricts = [strict_of(r) for r in scored]
    walls = [w for w in (wall_of(r) for r in scored) if w is not None]
    counts: dict[str, int] = {}
    for r in recs:
        st = verdict_of(r).get("status", "?")
        counts[st] = counts.get(st, 0) + 1
    q_sem = sum(sems) / len(sems) if sems else 0.0
    q_strict = sum(stricts) / len(stricts) if stricts else 0.0
    ci_lo, ci_hi = bootstrap_ci(sems)
    n_scored = len(scored)
    n_total = len(recs)
    coverage = (n_scored / n_total) if n_total else 0.0
    return {"n_scored": n_scored, "n_total": n_total,
            "q_sem": q_sem, "q_strict": q_strict,
            "ci_lo": ci_lo, "ci_hi": ci_hi, "counts": counts,
            "coverage": coverage,
            "insufficient_coverage": coverage < 0.9,
            "median_wall": statistics.median(walls) if walls else None}


def compute_tables(records: list[dict]) -> tuple[dict, dict, list[dict]]:
    """Return (per_test, per_model, perf_rows).

    per_test[tid] = ranked list of per-model summaries (sorted by q_sem desc).
    per_model[tag] = {"tests": {tid: summary}, "identity": {...}}.
    """
    by_test_model: dict[str, dict[str, list]] = {}
    identities: dict[str, dict] = {}
    for r in records:
        tid = test_of(r)
        tag = model_of(r)
        by_test_model.setdefault(tid, {}).setdefault(tag, []).append(r)
        if tag not in identities and r.get("identity"):
            identities[tag] = r["identity"]
    per_test: dict[str, list] = {}
    per_model: dict[str, dict] = {}
    for tid, m in by_test_model.items():
        rows = []
        for tag, recs in m.items():
            s = summarize_group(recs)
            s["model"] = tag
            rows.append(s)
            per_model.setdefault(tag, {"tests": {}, "identity": identities.get(tag, {})})
            per_model[tag]["tests"][tid] = s
        rows.sort(key=lambda r: (-r["q_sem"], -r["n_scored"], r["model"]))
        per_test[tid] = rows
    # perf rows from PERF records
    perf_rows = []
    for tag, pm in per_model.items():
        perf_recs = []
        for tid in ("PERF",):
            for r in by_test_model.get(tid, {}).get(tag, []):
                perf_recs.append(r)
        cold = [wall_of(r) for r in perf_recs
                if "cold" in (r.get("key", "")) and wall_of(r) is not None]
        ttfts, ptoks, gtoks, peaks, offloads, throttles = [], [], [], [], [], []
        for r in perf_recs:
            t = r.get("timing") or {}
            res = r.get("resources") or {}
            det = (r.get("verdict") or {}).get("details") or {}
            load = r.get("load_info") or {}
            for src, dst in (("ttft_s", ttfts), ("prompt_tok_s", ptoks),
                             ("gen_tok_s", gtoks)):
                v = t.get(src)
                try:
                    if v is not None:
                        dst.append(float(v))
                except (TypeError, ValueError):
                    pass
            v = res.get("vram_peak_mb")
            try:
                if v is not None:
                    peaks.append(float(v))
            except (TypeError, ValueError):
                pass
            # FIX_A.3: offload_ratio from /api/ps (details or load_info)
            for src in (det, load):
                try:
                    ov = src.get("offload_ratio")
                    if ov is not None:
                        offloads.append(float(ov))
                        break
                except (TypeError, ValueError):
                    continue
            th = res.get("throttle")
            if th is not None:
                throttles.append(th)
        import statistics as _st
        off_med = _st.median(offloads) if offloads else ""
        thr_val: object = ""
        if throttles:
            thr_val = any(bool(x) for x in throttles)
        perf_rows.append({"tag": tag,
                          "cold_load_s": _st.median(cold) if cold else "",
                          "ttft_s": _st.median(ttfts) if ttfts else "",
                          "prompt_tok_s": _st.median(ptoks) if ptoks else "",
                          "gen_tok_s": _st.median(gtoks) if gtoks else "",
                          "vram_peak_mb": max(peaks) if peaks else "",
                          "offload_ratio": off_med,
                          "throttle": thr_val})
    return per_test, per_model, perf_rows


def _home_map_for_report() -> dict:
    """Return {test_id: home_tag} via registry discovery; {} when unavailable."""
    try:
        from bench import registry as _reg
        import os as _os
        root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
        tdir = _os.path.join(root, "bench", "tests")
        if not _os.path.isdir(tdir):
            return {}
        mods = _reg.discover(tdir)
        inv = {v: k for k, v in _reg.home_model_map(mods).items()}
        return inv
    except Exception:
        return {}


def home_verdicts(per_test: dict, records: list[dict]) -> dict:
    """HOME_WIN/HOME_TIE/HOME_LOSS per home test vs best competitor.

    FIX_A.7: uses only cases scored for BOTH home and competitor (pairwise
    common set). Rows with coverage < 0.9 are excluded as insufficient
    coverage. Falls back to best-vs-second on the global common set when the
    home model mapping is unavailable (e.g. synthetic unit tests).
    """
    out: dict = {}
    home_map = _home_map_for_report()
    for tid, rows in per_test.items():
        if tid not in HOME_SET or len(rows) < 2:
            continue
        by_model_case: dict[str, dict[str, float]] = {}
        for r in records:
            if test_of(r) != tid:
                continue
            if verdict_of(r).get("status") not in SCORED:
                continue
            key = r.get("key", "")
            case = key.split("|")[4] if len(key.split("|")) >= 5 else ""
            by_model_case.setdefault(model_of(r), {})[case] = sem_of(r)
        if len(by_model_case) < 2:
            continue
        # coverage filter: keep only rows with coverage >= 0.9 when known
        cov_by_model = {row.get("model"): row for row in rows}
        eligible_models = [m for m in by_model_case
                           if not cov_by_model.get(m, {}).get("insufficient_coverage", False)]
        if len(eligible_models) < 2:
            # fall back to all models if filtering removes too much
            eligible_models = list(by_model_case)
        home_tag = home_map.get(tid)
        if home_tag and home_tag in by_model_case and home_tag in eligible_models:
            home_cases = by_model_case[home_tag]
            best_comp = None
            best_mean = None
            best_common: list[str] = []
            for m in eligible_models:
                if m == home_tag:
                    continue
                common = sorted(set(home_cases) & set(by_model_case[m]))
                if not common:
                    continue
                mean = sum(by_model_case[m][c] for c in common) / len(common)
                if best_mean is None or mean > best_mean:
                    best_mean = mean
                    best_comp = m
                    best_common = common
            if best_comp is None:
                continue
            a = [home_cases[c] for c in best_common]
            c = [by_model_case[best_comp][cc] for cc in best_common]
            _mean, lo, hi = paired_diff_ci(a, c)
            verdict = "HOME_WIN" if lo > 0 else ("HOME_LOSS" if hi < 0 else "HOME_TIE")
            out[tid] = {"best": home_tag, "second": best_comp,
                        "verdict": verdict, "common_n": len(best_common),
                        "ci_lo": lo, "ci_hi": hi}
            continue
        # fallback: best vs second on the global common set (legacy unit tests)
        filt = {m: v for m, v in by_model_case.items() if m in eligible_models}
        if len(filt) < 2:
            filt = by_model_case
        common = set.intersection(*[set(v) for v in filt.values()])
        common = sorted(common)
        if not common:
            continue
        means = {m: sum(filt[m][c] for c in common) / len(common)
                 for m in filt}
        top = sorted(means, key=lambda m: -means[m])
        best, second = top[0], top[1]
        a = [filt[best][c] for c in common]
        c = [filt[second][cc] for cc in common]
        _mean, lo, hi = paired_diff_ci(a, c)
        verdict = "HOME_WIN" if lo > 0 else ("HOME_LOSS" if hi < 0 else "HOME_TIE")
        out[tid] = {"best": best, "second": second, "verdict": verdict,
                    "common_n": len(common), "ci_lo": lo, "ci_hi": hi}
    return out


def write_report(run_dir: str) -> dict:
    records = load_records(run_dir)
    per_test, per_model, perf_rows = compute_tables(records)
    hv = home_verdicts(per_test, records)
    os.makedirs(os.path.join(run_dir, "models"), exist_ok=True)
    # results.csv
    with open(os.path.join(run_dir, "results.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "test", "n_scored", "n_total", "q_sem", "q_strict",
                    "ci_lo", "ci_hi", "coverage", "median_wall_s"])
        for tid, rows in sorted(per_test.items()):
            for r in rows:
                cov = (r["n_scored"] / r["n_total"]) if r["n_total"] else 0.0
                w.writerow([r["model"], tid, r["n_scored"], r["n_total"],
                            f"{r['q_sem']:.4f}", f"{r['q_strict']:.4f}",
                            f"{r['ci_lo']:.4f}", f"{r['ci_hi']:.4f}",
                            f"{cov:.3f}",
                            f"{r['median_wall']:.2f}" if r["median_wall"] is not None else ""])
    # perf.csv
    with open(os.path.join(run_dir, "perf.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tag", "cold_load_s", "ttft_s", "prompt_tok_s", "gen_tok_s",
                    "vram_peak_mb", "offload_ratio", "throttle"])
        for pr in sorted(perf_rows, key=lambda r: r["tag"]):
            w.writerow([pr["tag"], pr["cold_load_s"], pr["ttft_s"],
                        pr["prompt_tok_s"], pr["gen_tok_s"], pr["vram_peak_mb"],
                        pr["offload_ratio"], pr["throttle"]])
    # errors.csv
    with open(os.path.join(run_dir, "errors.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "model", "test", "status", "sub_reason",
                    "attribution", "flags"])
        for r in records:
            v = verdict_of(r)
            if v.get("status") not in SCORED and v.get("status") != "OK":
                w.writerow([r.get("key", ""), model_of(r), test_of(r),
                            v.get("status", ""), v.get("sub_reason", ""),
                            v.get("attribution", ""),
                            ";".join(r.get("flags", []))])
    # per-model files
    for tag, pm in per_model.items():
        safe = tag.replace(":", "_").replace("/", "_")
        fail_counts: dict[str, int] = {}
        flags_seen: dict[str, int] = {}
        for tid, s in pm["tests"].items():
            for st, n in s["counts"].items():
                if st not in SCORED or st != "OK":
                    fail_counts[st] = fail_counts.get(st, 0) + n
        for r in records:
            if model_of(r) == tag:
                for fl in r.get("flags", []):
                    flags_seen[fl] = flags_seen.get(fl, 0) + 1
        # FIX_A.3: per-model load_info aggregated from PERF records
        load_info: dict = {}
        for r in records:
            if model_of(r) == tag and test_of(r) == "PERF":
                det = ((r.get("verdict") or {}).get("details")) or {}
                li = r.get("load_info") or {}
                for src in (li, det):
                    for k in ("size", "size_vram", "offload_ratio",
                              "context_length", "layers_gpu", "layers_total"):
                        if load_info.get(k) is None and src.get(k) is not None:
                            load_info[k] = src.get(k)
        data = {"model": tag, "identity": pm["identity"], "tests": pm["tests"],
                "failures_by_status": fail_counts, "flags": flags_seen,
                "load_info": load_info,
                "home_verdicts": {tid: v for tid, v in hv.items()
                                  if v.get("best") == tag}}
        with open(os.path.join(run_dir, "models", safe + ".json"), "w",
                   encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        lines = [f"# {tag}", ""]
        ident = pm["identity"] or {}
        lines.append(f"- digest: {ident.get('digest', 'unknown')}")
        lines.append(f"- ollama: {ident.get('ollama_version', 'unknown')}")
        if load_info:
            lines.append(f"- load: {load_info}")
        lines.append("")
        lines.append("## Tests")
        for tid in sorted(pm["tests"]):
            s = pm["tests"][tid]
            cov_mark = " (insufficient coverage)" if s.get("insufficient_coverage") else ""
            lines.append(f"- {tid}: Q_sem={s['q_sem']:.3f} "
                         f"Q_strict={s['q_strict']:.3f} n={s['n_scored']}/{s['n_total']} "
                         f"coverage={s.get('coverage', 0.0):.3f} "
                         f"CI=[{s['ci_lo']:.3f},{s['ci_hi']:.3f}] "
                         f"counts={s['counts']}{cov_mark}")
        lines.append("")
        lines.append(f"## Failures: {fail_counts}")
        lines.append(f"## Flags: {flags_seen}")
        with open(os.path.join(run_dir, "models", safe + ".md"), "w",
                   encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    # summary.md
    deferred = _deferred_section()
    overview = run_overview(records)
    lines = ["# NIGHT-1 summary", "", "## Run overview", ""]
    lines.append(f"- models run: {overview['n_models']} "
                 f"({', '.join(overview['models']) if overview['models'] else 'none'})")
    lines.append(f"- tests run: {overview['n_tests']} "
                 f"({', '.join(overview['tests']) if overview['tests'] else 'none'})")
    lines.append(f"- records: {len(records)}")
    lines.append(f"- wall time total (sum wall_s): {overview['wall_total_s']:.1f} s")
    lines.append(f"- NOT_RUN_BUDGET: {overview['not_run_budget']}")
    lines.append("- counts by status:")
    for st in sorted(overview["counts"]):
        lines.append(f"  - {st}: {overview['counts'][st]}")
    lines.append("")
    lines.append("## Per-test ranking (by Q_sem)")
    for tid in sorted(per_test):
        if tid == "PERF":  # speed/load rows live in perf.csv, not in the quality ranking
            continue
        lines.append(f"### {tid}")
        # rows with only UNSUPPORTED_CAPABILITY / NOT_RUN_BUDGET records are listed, never ranked
        def _only(r, sts):
            c = r.get("counts") or {}
            return bool(c) and set(c) <= sts
        unsup = sorted(r["model"] for r in per_test[tid] if _only(r, {"UNSUPPORTED_CAPABILITY"}))
        notrun = sorted(r["model"] for r in per_test[tid]
                        if _only(r, {"NOT_RUN_BUDGET", "UNSUPPORTED_CAPABILITY"})
                        and not _only(r, {"UNSUPPORTED_CAPABILITY"}))
        rows = [r for r in per_test[tid] if r["model"] not in unsup and r["model"] not in notrun]
        # ranked: sufficient coverage first (sorted by Q_sem), insufficient last
        ranked = sorted([r for r in rows
                         if not r.get("insufficient_coverage")],
                        key=lambda r: (-r["q_sem"], -r["n_scored"], r["model"]))
        unranked = sorted([r for r in rows
                           if r.get("insufficient_coverage")],
                          key=lambda r: (-r["q_sem"], -r["n_scored"], r["model"]))
        for r in ranked + unranked:
            mark = (" [insufficient coverage - not ranked]"
                    if r.get("insufficient_coverage") else "")
            lines.append(f"- {r['model']}: Q_sem={r['q_sem']:.3f} "
                         f"Q_strict={r['q_strict']:.3f} "
                         f"n={r['n_scored']}/{r['n_total']} "
                         f"cases={r['n_total']} coverage={r.get('coverage', 0.0):.3f} "
                         f"CI=[{r['ci_lo']:.3f},{r['ci_hi']:.3f}]{mark}")
        if unsup:
            lines.append(f"- UNSUPPORTED (not ranked): {', '.join(unsup)}")
        if notrun:
            lines.append(f"- NOT_RUN_BUDGET (not ranked): {', '.join(notrun)}")
        if tid in hv:
            v = hv[tid]
            lines.append(f"  HOME verdict: {v['verdict']} "
                         f"(best={v['best']} vs {v['second']}, "
                         f"common_n={v['common_n']})")
    lines.append("")
    lines.append("## DEFERRED")
    lines.append(deferred)
    with open(os.path.join(run_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return {"per_test": per_test, "per_model": per_model,
            "home_verdicts": hv, "n_records": len(records),
            "overview": overview}


def run_overview(records: list[dict]) -> dict:
    """Top overview table (FIX_A.7): models/tests run, status counts, wall, budget skips."""
    models = sorted({model_of(r) for r in records if model_of(r) != "unknown"})
    tests = sorted({test_of(r) for r in records})
    counts: dict[str, int] = {}
    wall_total = 0.0
    for r in records:
        st = verdict_of(r).get("status", "?")
        counts[st] = counts.get(st, 0) + 1
        w = wall_of(r)
        if w is not None:
            try:
                wall_total += float(w)
            except (TypeError, ValueError):
                pass
    return {"n_models": len(models), "models": models,
            "n_tests": len(tests), "tests": tests,
            "counts": counts, "wall_total_s": wall_total,
            "not_run_budget": counts.get("NOT_RUN_BUDGET", 0)}


def _deferred_section() -> str:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    elig_path = os.path.join(root, "config", "eligibility_night.json")
    try:
        with open(elig_path, encoding="utf-8") as f:
            elig = json.load(f)
        deferred = elig.get("_deferred", {})
        if not deferred:
            return "none recorded."
        lines = []
        for name in sorted(deferred):
            info = deferred[name]
            if isinstance(info, dict):
                lines.append(f"- {name}: {info.get('reason', '')}")
            else:
                lines.append(f"- {name}: {info}")
        return "\n".join(lines)
    except Exception:
        return ("6 LM Studio models (runtime not initialized) and "
                "6 Specialists (not installed).")


def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Write NIGHT-1 report")
    p.add_argument("run_id", help="run id or path to run dir")
    p.add_argument("--results-root", default=None)
    a = p.parse_args(argv)
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cand = a.run_id if os.path.isdir(a.run_id) else os.path.join(
        a.results_root or os.path.join(root, "results"), a.run_id)
    write_report(cand)
    print(f"report written to {cand}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
