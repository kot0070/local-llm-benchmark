"""Generator for HOME-17 (R1 constraint optimisation). Owner: TASK_B1."""
from __future__ import annotations

import hashlib
import json
import random
from itertools import permutations, product
from pathlib import Path

TEST_ID = "HOME-17"
SEED = 1417
VERSION = "n1"

JSON_SUFFIX = ("Output a single JSON object and nothing else (no code fences, "
               "no explanation).")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_cases_and_manifest(out_dir: Path, cases: list[dict]) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    cases_path = out_dir / "cases.jsonl"
    with open(cases_path, "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, sort_keys=True, ensure_ascii=False) + "\n")
    files = {"cases.jsonl": sha256_file(cases_path)}
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_17.py",
                "version": VERSION, "n_cases": len(cases), "files": files}
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def interleave(easy, medium, hard):
    out: list[dict] = []
    lists = [list(easy), list(medium), list(hard)]
    while any(lists):
        for lst in lists:
            if lst:
                out.append(lst.pop(0))
    return out


# ---------------- scheduling ----------------

def _schedule_makespan(assign, order, durations, prec):
    start, finish = {}, {}
    machine_free = [0, 0]
    pred_of = {j: [] for j in durations}
    for a, b in prec:
        pred_of[b].append(a)
    for j in order:
        m = assign[j]
        est = machine_free[m]
        for p in pred_of[j]:
            est = max(est, finish[p])
        start[j], finish[j] = est, est + durations[j]
        machine_free[m] = finish[j]
    return max(finish.values()), start


def _topo_orders(jobs, prec):
    preds = {j: set() for j in jobs}
    for a, b in prec:
        preds[b].add(a)
    out = []
    def rec(path, remaining):
        if not remaining:
            out.append(list(path))
            return
        for j in list(remaining):
            if preds[j] <= set(path):
                rec(path + [j], [x for x in remaining if x != j])
    rec([], list(jobs))
    return out


def _solve_schedule(durations, eligible, prec):
    jobs = list(durations)
    orders = _topo_orders(jobs, prec)
    best, best_sol = None, None
    for assign_vals in product([0, 1], repeat=len(jobs)):
        assign = dict(zip(jobs, assign_vals))
        if any(assign[j] not in eligible.get(j, [0, 1]) for j in jobs):
            continue
        for order in orders:
            mk, start = _schedule_makespan(assign, order, durations, prec)
            if best is None or mk < best:
                best = mk
                best_sol = {"machine": dict(assign), "start": dict(start)}
    return best, best_sol


def _solve_schedule_alt(durations, eligible, prec):
    # Independent enumeration: different order, machines outer loop swapped.
    jobs = list(reversed(list(durations)))
    orders = _topo_orders(list(durations), prec)
    best = None
    for order in reversed(orders):
        for assign_vals in product([0, 1], repeat=len(jobs)):
            assign = dict(zip(jobs, assign_vals))
            if any(assign[j] not in eligible.get(j, [0, 1]) for j in jobs):
                continue
            mk, _ = _schedule_makespan(assign, list(order), durations, prec)
            if best is None or mk < best:
                best = mk
    return best


def _gen_schedule(rng, tier):
    if tier == "easy":
        jobs = ["A", "B", "C", "D"]
        durations = {j: rng.randint(2, 5) for j in jobs}
        prec = [("A", "B"), ("A", "C")]
        eligible = {j: [0, 1] for j in jobs}
    elif tier == "medium":
        jobs = ["A", "B", "C", "D", "E"]
        durations = {j: rng.randint(2, 6) for j in jobs}
        prec = [("A", "C"), ("B", "C"), ("C", "D")]
        eligible = {j: [0, 1] for j in jobs}
        eligible["E"] = [1]
    else:
        jobs = ["A", "B", "C", "D", "E", "F"]
        durations = {j: rng.randint(3, 7) for j in jobs}
        prec = [("A", "D"), ("B", "D"), ("C", "E"), ("D", "F"), ("E", "F")]
        eligible = {j: [0, 1] for j in jobs}
        eligible["B"] = [0]
    best, sol = _solve_schedule(durations, eligible, prec)
    best2 = _solve_schedule_alt(durations, eligible, prec)
    assert best == best2 and best is not None and sol, "schedule verification failed"
    desc = (f"Two machines M0 and M1 process jobs {', '.join(jobs)}. Durations: "
            + ", ".join(f"{j}={durations[j]}" for j in jobs) + ". Precedence "
            + "(must finish before next starts): "
            + ", ".join(f"{a} before {b}" for a, b in prec) + ". Machine eligibility: "
            + ", ".join(f"{j} on {eligible[j]}" for j in jobs)
            + ". Minimize the makespan (time the last job finishes). Time starts at 0.")
    fmt = ('Output a single JSON object of the form {"machine": {"A": 0, ...}, '
           '"start": {"A": 0, ...}} with the chosen machine (0 or 1) and integer '
           'start time of every job. ' + JSON_SUFFIX)
    return desc + "\n\n" + fmt, {"kind": "schedule", "optimum": best,
                                 "data": {"durations": durations, "eligible": eligible,
                                          "precedences": [list(p) for p in prec]}}, sol


# ---------------- assignment ----------------

def _solve_assign(people, slots, scores, fixed, forbidden):
    best, best_sol = None, None
    for perm in permutations(slots):
        asg = dict(zip(people, perm))
        if any(asg[p] != s for p, s in fixed.items()):
            continue
        if any(asg[p] == s for p, s in forbidden):
            continue
        total = sum(scores[p][s] for p, s in asg.items())
        if best is None or total > best:
            best, best_sol = total, {"assignment": dict(asg)}
    return best, best_sol


def _gen_assign(rng, tier):
    people = ["Ada", "Boris", "Cleo", "Dan", "Eva"]
    slots = ["S1", "S2", "S3", "S4", "S5"]
    scores = {p: {s: rng.randint(1, 10) for s in slots} for p in people}
    fixed = {"Ada": "S1"} if tier != "hard" else {"Ada": "S1", "Eva": "S5"}
    forbidden = [("Boris", "S3"), ("Dan", "S2")]
    if tier == "hard":
        forbidden.append(("Cleo", "S4"))
    best, sol = _solve_assign(people, slots, scores, fixed, forbidden)
    # Independent check: reversed people order, same optimum required.
    best2, _ = _solve_assign(list(reversed(people)), slots, scores, fixed, forbidden)
    assert best == best2 and best is not None and sol, "assign verification failed"
    desc = (f"Assign 5 people {', '.join(people)} to 5 slots {', '.join(slots)} "
            f"(one person per slot). Preference scores:\n"
            + "\n".join(f"{p}: " + ", ".join(f"{s}={scores[p][s]}" for s in slots)
                        for p in people)
            + f"\nFixed: " + "; ".join(f"{p} must take {s}" for p, s in fixed.items())
            + f". Forbidden: " + "; ".join(f"{p} cannot take {s}" for p, s in forbidden)
            + ". Maximize the total preference score.")
    fmt = ('Output a single JSON object of the form {"assignment": '
           '{"<person>": "<slot>", ...}} mapping every person to a slot. ' + JSON_SUFFIX)
    return desc + "\n\n" + fmt, {"kind": "assign", "optimum": best,
                                 "data": {"people": people, "slots": slots,
                                          "scores": scores, "fixed": fixed,
                                          "forbidden": [list(f) for f in forbidden]}}, sol


# ---------------- selection ----------------

def _solve_select(items, budget, exclusions, required, atleast):
    excl = {tuple(sorted(e)) for e in exclusions}
    best, best_sol = None, None
    ids = [i["id"] for i in items]
    for mask in range(1 << len(ids)):
        chosen = [ids[k] for k in range(len(ids)) if mask & (1 << k)]
        cost = sum(next(i["cost"] for i in items if i["id"] == x) for x in chosen)
        if cost > budget:
            continue
        if any(a in chosen and b in chosen for a, b in excl):
            continue
        if any(r not in chosen for r in required):
            continue
        if atleast and sum(1 for x in atleast["group"] if x in chosen) < atleast["k"]:
            continue
        val = sum(next(i["value"] for i in items if i["id"] == x) for x in chosen)
        if best is None or val > best:
            best, best_sol = val, {"chosen": sorted(chosen)}
    return best, best_sol


def _gen_select(rng, tier):
    if tier == "easy":
        items = [{"id": f"P{i}", "cost": rng.randint(2, 6), "value": rng.randint(3, 9)}
                 for i in range(6)]
        budget = 12
        exclusions = [["P0", "P1"]]
        required = []
        atleast = {}
    elif tier == "medium":
        items = [{"id": f"P{i}", "cost": rng.randint(2, 8), "value": rng.randint(2, 10)}
                 for i in range(8)]
        budget = 18
        exclusions = [["P0", "P2"], ["P3", "P5"]]
        required = ["P1"]
        atleast = {}
    else:
        items = [{"id": f"P{i}", "cost": rng.randint(3, 9), "value": rng.randint(3, 10)}
                 for i in range(9)]
        budget = 22
        exclusions = [["P0", "P4"], ["P2", "P6"], ["P5", "P8"]]
        required = ["P3"]
        atleast = {"group": ["P0", "P1", "P2"], "k": 1}
    best, sol = _solve_select(items, budget, exclusions, required, atleast)
    best2, _ = _solve_select(list(reversed(items)), budget, exclusions, required, atleast)
    assert best == best2 and best is not None and sol and sol["chosen"], \
        "select verification failed"
    lines = "\n".join(f'{i["id"]}: cost={i["cost"]}, value={i["value"]}' for i in items)
    desc = (f"Choose a subset of projects to maximize total value. Projects:\n{lines}\n"
            f"Budget (total cost at most {budget}). "
            f"Exclusions (never both): " + (", ".join(f"{a}+{b}" for a, b in exclusions) or "none")
            + f". Required: " + (", ".join(required) or "none")
            + (f'. At least {atleast["k"]} of {", ".join(atleast["group"])}.' if atleast else "."))
    fmt = ('Output a single JSON object of the form {"chosen": ["P0", ...]} '
           'listing the chosen project ids. ' + JSON_SUFFIX)
    return desc + "\n\n" + fmt, {"kind": "select", "optimum": best,
                                 "data": {"items": items, "budget": budget,
                                          "exclusions": exclusions, "required": required,
                                          "atleast": atleast}}, sol


def build_cases():
    rng = random.Random(SEED)
    plan = [("easy", "assign"), ("easy", "select"), ("medium", "schedule"),
            ("medium", "assign"), ("hard", "schedule"), ("hard", "select")]
    gens = {"schedule": _gen_schedule, "assign": _gen_assign, "select": _gen_select}
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for i, (tier, kind) in enumerate(plan):
        prompt, expected, gold = gens[kind](rng, tier)
        # Verify gold passes the real validator checker.
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from bench.tests.home_17 import check_solution
        valid, objective, violations = check_solution(
            expected["kind"], json.loads(json.dumps(gold)), expected["data"])
        assert valid and objective == expected["optimum"], (kind, violations)
        by_tier[tier].append({
            "id": f"tmp-{i}",
            "test_id": TEST_ID,
            "tier": tier,
            "lang": "en",
            "input": {"prompt": prompt, "kind": kind},
            "expected": expected,
            "meta": {"gold": gold},
        })
    cases = interleave(by_tier["easy"], by_tier["medium"], by_tier["hard"])
    for j, c in enumerate(cases):
        c["id"] = f"HOME-17-{j + 1:02d}"
    return cases


def main() -> Path:
    out_dir = Path(__file__).resolve().parents[1] / "fixtures" / TEST_ID
    cases = build_cases()
    assert len(cases) == 6, len(cases)
    counts = {"easy": 0, "medium": 0, "hard": 0}
    for c in cases:
        counts[c["tier"]] += 1
    assert counts == {"easy": 2, "medium": 2, "hard": 2}, counts
    write_cases_and_manifest(out_dir, cases)
    return out_dir


if __name__ == "__main__":
    print(main())
