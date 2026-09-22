"""Generator for HOME-13 (R0 word problems, numeric answers). Owner: TASK_B1."""
from __future__ import annotations

import hashlib
import json
import random
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

TEST_ID = "HOME-13"
SEED = 1413
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
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_13.py",
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


def _q2(x) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _fmt_money(x: float) -> str:
    return f"{x:.2f}"


def _discount(rng, tier):
    price = rng.choice([120, 240, 360, 480, 850, 1250, 60, 1500])
    disc = rng.choice([10, 15, 20, 25, 30])
    tax = rng.choice([0, 5, 8, 10])
    a = price * (1 - disc / 100)
    b = a * (1 + tax / 100)
    ans = _q2(b)
    check = _q2(Decimal(str(price)) * (Decimal(100 - disc) / 100) * (Decimal(100 + tax) / 100))
    assert ans == check, "discount verification failed"
    prompt = (
        f"A shop lists a jacket at ${price}. There is a {disc}% seasonal discount, "
        f"and then a {tax}% sales tax is applied to the discounted price. "
        f"What is the final price in dollars? Give the amount to two decimals.\n{BOXED_SUFFIX}")
    return prompt, ans, 0.01


def _work_rate(rng, tier):
    if tier == "easy":
        rate = rng.choice([12, 15, 20])
        hours = rng.choice([3, 4, 5, 6])
        workers = 1
        ans = float(rate * hours)
        prompt = (
            f"A typist types {rate} pages per hour and works for {hours} hours. "
            f"How many pages are typed in total?\n{BOXED_SUFFIX}")
        assert ans == float(Decimal(rate) * Decimal(hours))
        return prompt, ans, 1e-6
    crew = rng.choice([2, 3, 4])
    rate = rng.choice([8, 10, 12])
    hours = rng.choice([5, 6, 8])
    ans = float(crew * rate * hours)
    check = float(Decimal(crew) * Decimal(rate) * Decimal(hours))
    assert ans == check
    prompt = (
        f"A crew of {crew} painters each paints {rate} square metres per hour. "
        f"They work together for {hours} hours. How many square metres do they paint "
        f"in total?\n{BOXED_SUFFIX}")
    return prompt, ans, 1e-6


def _unit_conv(rng, tier):
    km = rng.choice([5, 12, 42, 100, 250])
    ans = float(km * 1000)
    assert ans == float(Decimal(km) * 1000)
    prompt = (
        f"A cycling route is {km} kilometres long. How many metres is that?\n{BOXED_SUFFIX}")
    return prompt, ans, 1e-6


def _schedule(rng, tier):
    dep_h, dep_m = rng.choice([(7, 15), (8, 40), (9, 5), (13, 20), (17, 45)])
    dur = rng.choice([95, 125, 150, 200, 260])
    arr = dep_h * 60 + dep_m + dur
    ah, am = divmod(arr, 60)
    check = (dep_h * 60 + dep_m) + dur
    assert arr == check
    prompt = (
        f"A train departs at {dep_h:02d}:{dep_m:02d} and the journey takes {dur} minutes "
        f"with no time-zone changes. At what time does it arrive? Give the answer as "
        f"hours and minutes after midnight, i.e. the number HHMM (for example 0935 for "
        f"09:35).\n{BOXED_SUFFIX}")
    return prompt, float(ah * 100 + am), 1e-6


def _money_split(rng, tier):
    total = rng.choice([120, 240, 360, 480, 600])
    n = rng.choice([3, 4, 5, 6])
    tip = rng.choice([0, 10, 15])
    ans = _q2(total * (1 + tip / 100) / n)
    check = _q2(Decimal(str(total)) * (Decimal(100 + tip) / 100) / Decimal(n))
    assert ans == check
    tip_txt = f" plus a {tip}% tip" if tip else ""
    prompt = (
        f"A restaurant bill of ${total}{tip_txt} is split equally among {n} friends. "
        f"How much does each pay in dollars? Give the amount to two decimals.\n{BOXED_SUFFIX}")
    return prompt, ans, 0.01


def _mixture(rng, tier):
    if tier == "easy":
        apples = rng.choice([6, 8, 10])
        price = rng.choice([2, 3, 4])
        ans = float(apples * price)
        assert ans == float(Decimal(apples) * Decimal(price))
        prompt = (
            f"Apples cost ${price} per kilogram. How much do {apples} kilograms cost "
            f"in dollars?\n{BOXED_SUFFIX}")
        return prompt, ans, 1e-6
    q1 = rng.choice([10, 20, 30])
    p1 = rng.choice([4, 5, 6])
    q2 = rng.choice([10, 15, 25])
    p2 = rng.choice([7, 8, 9])
    ans = _q2((q1 * p1 + q2 * p2) / (q1 + q2))
    check = _q2((Decimal(q1) * Decimal(p1) + Decimal(q2) * Decimal(p2)) / Decimal(q1 + q2))
    assert ans == check
    prompt = (
        f"A grocer mixes {q1} kg of coffee at ${p1} per kg with {q2} kg at ${p2} per kg. "
        f"What is the price per kilogram of the mixture in dollars? Give the amount to "
        f"two decimals.\n{BOXED_SUFFIX}")
    return prompt, ans, 0.01


def _sharing(rng, tier):
    total = rng.choice([100, 150, 200, 300])
    ratio_a = rng.choice([1, 2, 3])
    ratio_b = rng.choice([1, 2, 3, 4])
    unit = total / (ratio_a + ratio_b)
    a = _q2(ratio_a * unit)
    check = _q2(Decimal(str(total)) * Decimal(ratio_a) / Decimal(ratio_a + ratio_b))
    assert a == check
    prompt = (
        f"${total} is shared between Anna and Ben in the ratio {ratio_a}:{ratio_b}. "
        f"How much does Anna receive in dollars? Give the amount to two decimals.\n{BOXED_SUFFIX}")
    return prompt, a, 0.01


def _interest(rng, tier):
    principal = rng.choice([1000, 2000, 5000])
    pct = rng.choice([3, 4, 5, 6])
    years = rng.choice([2, 3, 4])
    ans = _q2(principal * (1 + pct / 100) ** years)
    check = _q2(Decimal(str(principal)) * (1 + Decimal(pct) / 100) ** years)
    assert ans == check, "interest verification failed"
    prompt = (
        f"${principal} is invested at {pct}% annual compound interest. What is its value "
        f"after {years} years in dollars? Give the amount to two decimals.\n{BOXED_SUFFIX}")
    return prompt, ans, 0.01


def build_cases():
    rng = random.Random(SEED)
    plan = [
        ("easy", _discount), ("easy", _work_rate), ("easy", _unit_conv),
        ("easy", _money_split), ("easy", _mixture), ("easy", _sharing),
        ("easy", _work_rate), ("medium", _discount), ("medium", _schedule),
        ("medium", _money_split), ("medium", _mixture), ("medium", _sharing),
        ("medium", _interest), ("medium", _unit_conv), ("hard", _discount),
        ("hard", _schedule), ("hard", _mixture), ("hard", _interest),
        ("hard", _money_split), ("hard", _sharing),
    ]
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for i, (tier, fn) in enumerate(plan):
        prompt, ans, tol = fn(rng, tier)
        gold = ("\\boxed{%s}" % _fmt_money(ans)) if tol == 0.01 else (
            "\\boxed{%d}" % int(ans) if float(ans).is_integer() else "\\boxed{%s}" % ans)
        by_tier[tier].append({
            "id": f"tmp-{i}",
            "test_id": TEST_ID,
            "tier": tier,
            "lang": "en",
            "input": {"prompt": prompt, "kind": fn.__name__},
            "expected": {"answer": ans, "tol": tol},
            "meta": {"gold_boxed": gold},
        })
    cases = interleave(by_tier["easy"], by_tier["medium"], by_tier["hard"])
    for j, c in enumerate(cases):
        c["id"] = f"HOME-13-{j + 1:02d}"
    return cases


def main() -> Path:
    out_dir = Path(__file__).resolve().parents[1] / "fixtures" / TEST_ID
    cases = build_cases()
    assert len(cases) == 20, len(cases)
    import re as _re
    for c in cases:
        assert c["input"]["prompt"].rstrip().endswith("\\boxed{}.")
        m = _re.search(r"\\boxed\{([^}]*)\}", c["meta"]["gold_boxed"])
        assert m, c["id"]
        assert abs(float(m.group(1)) - c["expected"]["answer"]) <= c["expected"]["tol"], c["id"]
    counts = {"easy": 0, "medium": 0, "hard": 0}
    for c in cases:
        counts[c["tier"]] += 1
    assert counts == {"easy": 7, "medium": 7, "hard": 6}, counts
    write_cases_and_manifest(out_dir, cases)
    return out_dir


if __name__ == "__main__":
    print(main())
