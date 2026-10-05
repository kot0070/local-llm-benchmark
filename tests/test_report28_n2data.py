"""F_N2DATA regression: NIGHT-2 TIMEOUT-never-scored cross-check (records vs group_n2).

Re-derives the two disputed per_test cells, the three NIGHT-2 overall
ratings and the failure-pattern counts directly from
results/night2_b/results.jsonl (night2- tags only) via bench.report and
compares them to analysis_en/group_n2.json + analysis_uk/group_n2.json.

PRE_FIX_* fixtures embed the buggy pre-fix values (TIMEOUT counted as
scored). Every test asserts the live group values both equal the
recomputation AND differ from the fixture, so each test is red on
pre-fix data and green now. Read-only: no file is written.
"""
import json
import os
import re

from bench import report as rep

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
N2_DIR = os.path.join(ROOT, "results", "night2_b")

# Buggy pre-fix values (TIMEOUT counted as scored + nomic rounding slip).
# Embedded fixture: the recomputation below provably differs from these,
# so a group file still carrying them fails every test here (red).
PRE_FIX_CELLS = {
    ("night2-qwen3-vl-8b:q4km", "HOME-24"): {"q_sem": 0.867, "n": "15/30"},
    ("night2-qwen3.5-9b:q4km", "HOME-16"): {"q_sem": 0.825, "n": "40/40"},
}
PRE_FIX_OVERALL = {
    "night2-qwen3-vl-8b:q4km": {"scored_records": 200, "ok_records": 155,
                                "ok_rate_pct": 77.5, "tests_scored": 22,
                                "mean_q_sem": 0.787, "rating_10": 7.8},
    "night2-qwen3.5-9b:q4km": {"scored_records": 276, "ok_records": 221,
                               "ok_rate_pct": 80.1, "tests_scored": 17,
                               "mean_q_sem": 0.745, "rating_10": 7.6},
    "night2-nomic-embed-code:q4km": {"scored_records": 70, "ok_records": 41,
                                     "ok_rate_pct": 58.6, "tests_scored": 2,
                                     "mean_q_sem": 0.842, "rating_10": 7.7},
}
N2_RATING_MODELS = ["night2-qwen3-vl-8b:q4km",
                    "night2-nomic-embed-code:q4km",
                    "night2-qwen3.5-9b:q4km"]


def n2_records():
    return [r for r in rep.load_records(N2_DIR)
            if (r.get("identity") or {}).get("tag", "").startswith("night2-")]


def load_group(lang):
    name = "analysis_en" if lang == "en" else "analysis_uk"
    with open(os.path.join(ROOT, name, "group_n2.json"),
              encoding="utf-8") as f:
        return {m["model"]: m for m in json.load(f)}


def recompute_cell(recs, tag, tid):
    sub = [r for r in recs
           if rep.model_of(r) == tag and rep.test_of(r) == tid]
    s = rep.summarize_group(sub)
    return round(s["q_sem"], 3), "%d/%d" % (s["n_scored"], s["n_total"])


def recompute_overall(recs, tag):
    sub = [r for r in recs
           if rep.model_of(r) == tag and rep.test_of(r) != "PERF"]
    scored = [r for r in sub if rep.verdict_of(r).get("status") in rep.SCORED]
    oks = sum(1 for r in scored if rep.verdict_of(r).get("status") == "OK")
    by_test = {}
    for r in scored:
        by_test.setdefault(rep.test_of(r), []).append(rep.sem_of(r))
    per_q = {t: sum(v) / len(v) for t, v in by_test.items()}
    mean = sum(per_q.values()) / len(per_q)
    okr = oks / len(scored)
    return {"scored_records": len(scored), "ok_records": oks,
            "ok_rate_pct": round(okr * 100, 1), "tests_scored": len(by_test),
            "mean_q_sem": round(mean, 3),
            "rating_10": round(10 * (0.7 * mean + 0.3 * okr), 1)}


def test_disputed_cells_equal_recomputation():
    recs = n2_records()
    g = load_group("en")
    for (tag, tid), pre in PRE_FIX_CELLS.items():
        q, n = recompute_cell(recs, tag, tid)
        # sensitivity: the recomputation provably differs from the fixture
        assert (q, n) != (pre["q_sem"], pre["n"]), (tag, tid)
        pt = [p for p in g[tag]["per_test"] if p["test_id"] == tid][0]
        assert (pt["q_sem"], pt["n"]) == (q, n), (tag, tid, pt)
        # fix landed: live group values differ from the pre-fix fixture
        assert (pt["q_sem"], pt["n"]) != (pre["q_sem"], pre["n"]), (tag, tid)


def test_overall_ratings_equal_recomputation():
    recs = n2_records()
    g = load_group("en")
    for tag in N2_RATING_MODELS:
        exp = recompute_overall(recs, tag)
        got = {k: g[tag]["overall"][k] for k in exp}
        assert got != PRE_FIX_OVERALL[tag], tag  # red on pre-fix values
        assert got == exp, (tag, got, exp)


def test_timeout_never_scored():
    assert "TIMEOUT" not in rep.SCORED
    recs = n2_records()
    timeouts = [r for r in recs
                if rep.verdict_of(r).get("status") == "TIMEOUT"]
    # 1x vl HOME-24 + 2x qwen3.5 HOME-16 + 1x nomic PERF (cold load)
    assert len(timeouts) == 4
    home_timeouts = [r for r in timeouts if rep.test_of(r) != "PERF"]
    assert len(home_timeouts) == 3
    g = load_group("en")
    for (tag, tid) in PRE_FIX_CELLS:
        sub = [r for r in recs
               if rep.model_of(r) == tag and rep.test_of(r) == tid]
        n_scored = sum(1 for r in sub
                       if rep.verdict_of(r).get("status") in rep.SCORED)
        n_timeout = sum(1 for r in sub
                        if rep.verdict_of(r).get("status") == "TIMEOUT")
        assert n_timeout >= 1, (tag, tid)
        pt = [p for p in g[tag]["per_test"] if p["test_id"] == tid][0]
        assert pt["n"] == "%d/%d" % (n_scored, len(sub)), (tag, tid)


def test_en_uk_numeric_parity():
    en = load_group("en")
    uk = load_group("uk")
    assert set(en) == set(uk)
    num = re.compile(r"-?\d+(?:\.\d+)?")

    def fields(o, path=""):
        if isinstance(o, str):
            yield path, o
            return
        if isinstance(o, list):
            for i, v in enumerate(o):
                yield from fields(v, "%s/%d" % (path, i))
        elif isinstance(o, dict):
            for k, v in o.items():
                yield from fields(v, "%s/%s" % (path, k))
        else:
            yield path, o

    for tag in en:
        de = dict(fields(en[tag]))
        du = dict(fields(uk[tag]))
        assert set(de) == set(du), tag
        for k in de:
            a, b = de[k], du[k]
            if isinstance(a, str) and isinstance(b, str):
                if k.endswith("example_quote"):
                    assert a == b, (tag, k)  # quotes byte-identical
                    continue
                norm = lambda s: re.sub(r"(?<=\d),(?=\d)", "", s)
                na = [float(x) for x in num.findall(norm(a))]
                nb = [float(x) for x in num.findall(norm(b))]
                assert len(na) == len(nb), (tag, k, na, nb)
                assert all(abs(x - y) < 1e-9 for x, y in zip(na, nb)), \
                    (tag, k, na, nb)
            else:
                assert a == b, (tag, k, a, b)


def test_failure_counts_match_records_no_timeout_pattern():
    recs = n2_records()
    g = load_group("en")
    for tag in N2_RATING_MODELS:
        sub = [r for r in recs
               if rep.model_of(r) == tag and rep.test_of(r) != "PERF"
               and rep.verdict_of(r).get("status") in rep.SCORED]
        counts = {}
        for r in sub:
            v = rep.verdict_of(r)
            pat = v.get("status") + ("[%s]" % v["sub_reason"]
                                     if v.get("sub_reason") else "")
            counts[pat] = counts.get(pat, 0) + 1
        for fa in g[tag]["failure_analysis"]:
            assert "TIMEOUT" not in fa["pattern"], (tag, fa["pattern"])
            assert fa["count"] == counts.get(fa["pattern"], 0), \
                (tag, fa["pattern"])
