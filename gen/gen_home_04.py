"""Generator for HOME-04 (R1 math, integer answers). Owner: TASK_B1."""
from __future__ import annotations

import hashlib
import json
import math
import random
from fractions import Fraction
from itertools import combinations
from pathlib import Path

TEST_ID = "HOME-04"
SEED = 1404
VERSION = "n1"

BOXED_SUFFIX = "Put the final answer within \\boxed{}."


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
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_04.py",
                "version": VERSION, "n_cases": len(cases), "files": files}
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def interleave(easy: list[dict], medium: list[dict], hard: list[dict]) -> list[dict]:
    out: list[dict] = []
    for trio in zip(easy, medium, hard):
        out.extend(trio)
    rest = []
    for lst in (easy, medium, hard):
        rest.extend(lst[len(out) // 3 + (1 if len(out) % 3 else 0):])
    # Simpler deterministic round-robin:
    out = []
    lists = [list(easy), list(medium), list(hard)]
    while any(lists):
        for lst in lists:
            if lst:
                out.append(lst.pop(0))
    return out


def _dp_paths(rows, cols, blocked):
    dp = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if (r, c) in blocked:
                dp[r][c] = 0
            elif r == 0 and c == 0:
                dp[r][c] = 1
            else:
                dp[r][c] = (dp[r - 1][c] if r else 0) + (dp[r][c - 1] if c else 0)
    return dp[rows - 1][cols - 1]


def _rec_paths(r, c, blocked, memo):
    if (r, c) in blocked or r < 0 or c < 0:
        return 0
    if r == 0 and c == 0:
        return 1
    if (r, c) in memo:
        return memo[(r, c)]
    v = _rec_paths(r - 1, c, blocked, memo) + _rec_paths(r, c - 1, blocked, memo)
    memo[(r, c)] = v
    return v


GRID_CONVENTION = ("cells are written as (row, column), 0-indexed, row 0 is "
                   "the top row, column 0 is the leftmost.")


def _lattice(rng, tier):
    if tier == "easy":
        rows, cols, nblock = 4, 4, 1
    elif tier == "medium":
        rows, cols, nblock = 5, 6, 2
    else:
        rows, cols, nblock = 7, 7, 5
    cells = [(r, c) for r in range(rows) for c in range(cols)
             if (r, c) not in ((0, 0), (rows - 1, cols - 1))]
    a = 0
    blocked = set()
    for _ in range(200):
        blocked = set(rng.sample(cells, nblock))
        a = _dp_paths(rows, cols, blocked)
        if a > 0:
            break
    assert a > 0, "lattice: no unblocked path found"
    b = _rec_paths(rows - 1, cols - 1, blocked, {})
    assert a == b, "lattice verification failed"
    bl = ", ".join(f"({r},{c})" for r, c in sorted(blocked))
    prompt = (
        f"A robot starts at the top-left corner of a {rows}x{cols} grid and must reach "
        f"the bottom-right corner, moving only right or down. "
        f"The grid has {rows} rows and {cols} columns of cells; {GRID_CONVENTION} "
        f"The cells {bl} are blocked "
        f"and cannot be entered. How many different valid paths are there?\n{BOXED_SUFFIX}")
    return prompt, a


def _digitprop(rng, tier):
    if tier == "easy":
        lo, hi, d, s = 1, 200, 7, 10
    elif tier == "medium":
        lo, hi = 100, 2000
        d, s = 13, 12
    else:
        lo, hi = 1000, 20000
        d, s = 17, 18
    def ok(n):
        return n % d == 0 and sum(map(int, str(n))) == s
    a = sum(1 for n in range(lo, hi + 1) if ok(n))
    b = len([n for n in range(lo, hi + 1) if n % d == 0 and sum(int(x) for x in str(n)) == s])
    assert a == b and a > 0, "digitprop verification failed"
    prompt = (
        f"How many integers n with {lo} <= n <= {hi} are divisible by {d} and have "
        f"digit sum equal to {s}?\n{BOXED_SUFFIX}")
    return prompt, a


def _modular(rng, tier):
    if tier == "easy":
        mods = [(3, rng.randint(0, 2)), (5, rng.randint(0, 4))]
    elif tier == "medium":
        mods = [(4, rng.randint(0, 3)), (7, rng.randint(0, 6))]
    else:
        mods = [(4, rng.randint(0, 3)), (5, rng.randint(0, 4)),
                (7, rng.randint(0, 6)), (9, rng.randint(0, 8))]
    brute = next(x for x in range(10**6) if all(x % m == r for m, r in mods))
    # Independent check via incremental CRT.
    x, step = mods[0][1], mods[0][0]
    for m, r in mods[1:]:
        while x % m != r:
            x += step
        step *= m
    assert x == brute, "modular verification failed"
    conds = " and ".join(f"x mod {m} = {r}" for m, r in mods)
    prompt = (
        f"Find the smallest non-negative integer x such that {conds}.\n{BOXED_SUFFIX}")
    return prompt, brute


def _incexc(rng, tier):
    # Hard counting: integers in 1..N divisible by at least one divisor.
    divs = sorted(rng.sample([3, 4, 5, 6, 7, 9, 10, 11], 4))
    N = 100000
    a = sum(1 for n in range(1, N + 1) if any(n % d == 0 for d in divs))
    # Independent check: inclusion-exclusion over non-empty subsets.
    b = 0
    for r in range(1, len(divs) + 1):
        for sub in combinations(divs, r):
            l = 1
            for d in sub:
                l = l * d // math.gcd(l, d)
            term = N // l
            b += term if r % 2 == 1 else -term
    assert a == b and a > 0, "incexc verification failed"
    listed = ", ".join(str(d) for d in divs)
    prompt = (
        f"How many integers n with 1 <= n <= {N} are divisible by at least "
        f"one of {listed}?\n{BOXED_SUFFIX}")
    return prompt, a


def _prob(rng, tier):
    if tier == "easy":
        reds, blues = 3, 2
        total = reds + blues
        fr = Fraction(reds * (reds - 1) + blues * (blues - 1), total * (total - 1))
        check = Fraction(reds, total) * Fraction(reds - 1, total - 1) + \
            Fraction(blues, total) * Fraction(blues - 1, total - 1)
        assert fr == check
        prompt = (
            f"An urn contains {reds} red and {blues} blue balls. Two balls are drawn at "
            f"random without replacement. The probability that both balls have the same "
            f"colour is p/q in lowest terms. Find p+q.\n{BOXED_SUFFIX}")
        return prompt, fr.numerator + fr.denominator
    elif tier == "medium":
        reds, blues, greens = 4, 3, 2
        total = reds + blues + greens
        fav = reds * (reds - 1) + blues * (blues - 1) + greens * (greens - 1)
        tot = total * (total - 1)
        fr = Fraction(fav, tot)
        check = Fraction(reds, total) * Fraction(reds - 1, total - 1) + \
            Fraction(blues, total) * Fraction(blues - 1, total - 1) + \
            Fraction(greens, total) * Fraction(greens - 1, total - 1)
        assert fr == check
        prompt = (
            f"An urn contains {reds} red, {blues} blue and {greens} green balls. Two balls "
            f"are drawn at random without replacement. The probability that both balls have "
            f"the same colour is p/q in lowest terms. Find p+q.\n{BOXED_SUFFIX}")
        return prompt, fr.numerator + fr.denominator
    elif tier == "hard":
        reds, blues, greens, yellows = 5, 4, 3, 3
        counts = [reds, blues, greens, yellows]
        # Brute force: enumerate every triple of balls.
        balls = [ci for ci, c in enumerate(counts) for _ in range(c)]
        same = sum(1 for t in combinations(balls, 3)
                   if t[0] == t[1] == t[2])
        # Independent check: sum of C(c, 3) over colours.
        expect = sum(c * (c - 1) * (c - 2) // 6 for c in counts)
        assert same == expect and same > 0, "prob verification failed"
        total = len(balls)
        fr = Fraction(same, total * (total - 1) * (total - 2) // 6)
        prompt = (
            f"An urn contains {reds} red, {blues} blue, {greens} green and {yellows} yellow "
            f"balls. Three balls are drawn at random without replacement. The probability that "
            f"all three balls have the same colour is p/q in lowest terms. Find p+q.\n{BOXED_SUFFIX}")
        return prompt, fr.numerator + fr.denominator


def _select(rng, tier):
    if tier == "easy":
        n, k, req, conf = 8, 3, 0, (1, 2)
    elif tier == "medium":
        n, k, req, conf = 10, 4, 0, (3, 7)
    else:
        # Hard: required member plus TWO forbidden pairs.
        n, k = 12, 5
        people = list(range(n))
        req = int(rng.choice(people))
        rest = [p for p in people if p != req]
        picked = rng.sample(rest, 4)
        confs = [(picked[0], picked[1]), (picked[2], picked[3])]
        a = sum(1 for c in combinations(people, k)
                if req in c and not any(x in c and y in c for x, y in confs))
        # Independent check: inclusion-exclusion (pairs are disjoint and
        # exclude req, so |req & pair| = C(n-3,k-3), |req & both| = C(n-5,k-5)).
        assert len(set(picked)) == 4 and req not in picked
        b = (math.comb(n - 1, k - 1) - 2 * math.comb(n - 3, k - 3)
             + math.comb(n - 5, k - 5))
        assert a == b and a > 0, "select verification failed"
        (c1, c2), (c3, c4) = confs
        prompt = (
            f"From {n} people a committee of {k} is chosen, one of whom must be "
            f"person {req}, but persons {c1} and {c2} refuse to serve together "
            f"and persons {c3} and {c4} refuse to serve together. How many valid "
            f"committees are possible?\n{BOXED_SUFFIX}")
        return prompt, a
    people = list(range(n))
    a = sum(1 for c in combinations(people, k)
            if not (conf[0] in c and conf[1] in c) and (req not in people or req in c or True))
    b = sum(1 for c in combinations(reversed(people), k)
            if not (conf[0] in c and conf[1] in c))
    assert a == b and a > 0, "select verification failed"
    prompt = (
        f"From {n} people a committee of {k} is chosen but persons {conf[0]} and "
        f"{conf[1]} refuse to serve together. How many valid committees are possible?\n{BOXED_SUFFIX}")
    return prompt, a


def _recur(rng, tier):
    if tier == "easy":
        a0, p, q, N = rng.randint(1, 5), 2, rng.randint(1, 5), 10
    elif tier == "medium":
        a0, p, q, N = rng.randint(1, 9), 3, rng.randint(1, 9), 8
    else:
        a0, p, q, N = rng.randint(2, 9), 2, rng.randint(5, 12), 20
    seq = [a0]
    for _ in range(N):
        seq.append(p * seq[-1] + q)
    a = seq[N]
    # Closed form check: a(N) = p^N*a0 + q*(p^N-1)/(p-1).
    b = (p ** N) * a0 + q * ((p ** N) - 1) // (p - 1)
    assert a == b, "recurrence verification failed"
    prompt = (
        f"A sequence is defined by a(0) = {a0} and a(n) = {p}*a(n-1) + {q} for n >= 1. "
        f"Find a({N}).\n{BOXED_SUFFIX}")
    return prompt, a


def build_cases():
    rng = random.Random(SEED)
    plan = [("easy", _lattice), ("easy", _digitprop), ("easy", _modular),
            ("easy", _prob), ("medium", _lattice), ("medium", _digitprop),
            ("medium", _select), ("medium", _recur), ("hard", _lattice),
            ("hard", _modular), ("hard", _incexc), ("hard", _select)]
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for i, (tier, fn) in enumerate(plan):
        prompt, ans = fn(rng, tier)
        assert isinstance(ans, int), f"non-integer answer for case {i}"
        gold = "\\boxed{%d}" % ans
        by_tier[tier].append({
            "id": f"HOME-04-{i + 1:02d}",
            "test_id": TEST_ID,
            "tier": tier,
            "lang": "en",
            "input": {"prompt": prompt, "kind": fn.__name__},
            "expected": {"answer": ans},
            "meta": {"gold_boxed": gold},
        })
    cases = interleave(by_tier["easy"], by_tier["medium"], by_tier["hard"])
    # Re-number ids in stratified order so ids match fixture order.
    for j, c in enumerate(cases):
        c["id"] = f"HOME-04-{j + 1:02d}"
    return cases


def main() -> Path:
    out_dir = Path(__file__).resolve().parents[1] / "fixtures" / TEST_ID
    cases = build_cases()
    assert len(cases) == 12
    # Self-verification: every gold parses back to the expected answer.
    import re as _re
    for c in cases:
        m = _re.search(r"\\boxed\{(-?\d+)\}", c["meta"]["gold_boxed"])
        assert m and int(m.group(1)) == c["expected"]["answer"], c["id"]
        assert c["input"]["prompt"].rstrip().endswith("\\boxed{}.")
        if c["input"]["kind"] == "_lattice":
            assert "0-indexed" in c["input"]["prompt"], c["id"]
    counts = {"easy": 0, "medium": 0, "hard": 0}
    for c in cases:
        counts[c["tier"]] += 1
    assert counts == {"easy": 4, "medium": 4, "hard": 4}, counts
    write_cases_and_manifest(out_dir, cases)
    return out_dir


if __name__ == "__main__":
    print(main())
