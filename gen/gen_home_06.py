"""Generator for HOME-06 (bug repair). Owner: TASK_B1."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

TEST_ID = "HOME-06"
SEED = 1406
VERSION = "n1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bench.validate import pysandbox  # noqa: E402

REPAIR_SUFFIX = ("Return the full corrected function in exactly one ```python fenced "
                 "block, followed by a final line `BUG_LINE: <n>` where <n> is the "
                 "1-based line number of the bug in the numbered code above, "
                 "and nothing else.")


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
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_06.py",
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


BUGS: list[dict] = [
    dict(tier="easy", task_id="sum_range", func="total_upto",
         title="Sum 1..n",
         ref=("def total_upto(n):\n"
              "    total = 0\n"
              "    for i in range(1, n + 1):\n"
              "        total += i\n"
              "    return total\n"),
         buggy=("def total_upto(n):\n"
                "    total = 0\n"
                "    for i in range(n):\n"
                "        total += i\n"
                "    return total\n"),
         bug_line=3, bug_kind="off-by-one",
         tests=[{"args": [5], "expected": 15},
                {"args": [1], "expected": 1},
                {"args": [0], "expected": 0},
                {"args": [10], "expected": 55},
                {"args": [100], "expected": 5050},
                {"args": [2], "expected": 3}]),
    dict(tier="easy", task_id="vowels", func="count_vowels",
         title="Count vowels",
         ref=("def count_vowels(s):\n"
              "    vowels = 'aeiouAEIOU'\n"
              "    n = 0\n"
              "    for ch in s:\n"
              "        if ch in vowels:\n"
              "            n += 1\n"
              "    return n\n"),
         buggy=("def count_vowels(s):\n"
                "    vowels = 'aeioAEIO'\n"
                "    n = 0\n"
                "    for ch in s:\n"
                "        if ch in vowels:\n"
                "            n += 1\n"
                "    return n\n"),
         bug_line=2, bug_kind="wrong edge case (missing letter)",
         tests=[{"args": ["hello"], "expected": 2},
                {"args": ["rhythm"], "expected": 0},
                {"args": [""], "expected": 0},
                {"args": ["UNIQUE"], "expected": 4},
                {"args": ["aeiou"], "expected": 5},
                {"args": ["bcdfg"], "expected": 0}]),
    dict(tier="easy", task_id="sorted_chk", func="is_sorted",
         title="Sorted check",
         ref=("def is_sorted(xs):\n"
              "    for i in range(len(xs) - 1):\n"
              "        if xs[i] > xs[i + 1]:\n"
              "            return False\n"
              "    return True\n"),
         buggy=("def is_sorted(xs):\n"
                "    for i in range(len(xs) - 1):\n"
                "        if xs[i] >= xs[i + 1]:\n"
                "            return False\n"
                "    return True\n"),
         bug_line=3, bug_kind="wrong comparator",
         tests=[{"args": [[1, 2, 3]], "expected": True},
                {"args": [[3, 2, 1]], "expected": False},
                {"args": [[]], "expected": True},
                {"args": [[1, 1, 2]], "expected": True},
                {"args": [[2, 2, 2]], "expected": True},
                {"args": [[1, 3, 2]], "expected": False}]),
    dict(tier="easy", task_id="fact", func="factorial",
         title="Factorial",
         ref=("def factorial(n):\n"
              "    result = 1\n"
              "    for i in range(2, n + 1):\n"
              "        result *= i\n"
              "    return result\n"),
         buggy=("def factorial(n):\n"
                "    result = 1\n"
                "    for i in range(2, n):\n"
                "        result *= i\n"
                "    return result\n"),
         bug_line=3, bug_kind="off-by-one",
         tests=[{"args": [0], "expected": 1},
                {"args": [1], "expected": 1},
                {"args": [5], "expected": 120},
                {"args": [3], "expected": 6},
                {"args": [7], "expected": 5040},
                {"args": [2], "expected": 2}]),
    dict(tier="medium", task_id="binsearch", func="binary_search",
         title="Binary search",
         ref=("def binary_search(xs, target):\n"
              "    lo, hi = 0, len(xs) - 1\n"
              "    while lo <= hi:\n"
              "        mid = (lo + hi) // 2\n"
              "        if xs[mid] == target:\n"
              "            return mid\n"
              "        elif xs[mid] < target:\n"
              "            lo = mid + 1\n"
              "        else:\n"
              "            hi = mid - 1\n"
              "    return -1\n"),
         buggy=("def binary_search(xs, target):\n"
                "    lo, hi = 0, len(xs)\n"
                "    while lo <= hi:\n"
                "        mid = (lo + hi) // 2\n"
                "        if xs[mid] == target:\n"
                "            return mid\n"
                "        elif xs[mid] < target:\n"
                "            lo = mid + 1\n"
                "        else:\n"
                "            hi = mid - 1\n"
                "    return -1\n"),
         bug_line=2, bug_kind="off-by-one (high bound)",
         tests=[{"args": [[1, 2, 3, 4, 5], 3], "expected": 2},
                {"args": [[1, 2, 3, 4, 5], 1], "expected": 0},
                {"args": [[1, 2, 3, 4, 5], 5], "expected": 4},
                {"args": [[1, 2, 3, 4, 5], 6], "expected": -1},
                {"args": [[], 1], "expected": -1},
                {"args": [[7], 7], "expected": 0},
                {"args": [[1, 3, 5, 7], 4], "expected": -1}]),
    dict(tier="medium", task_id="mutable_def", func="append_item",
         title="Mutable default argument",
         ref=("def append_item(item, acc=None):\n"
              "    if acc is None:\n"
              "        acc = []\n"
              "    acc.append(item)\n"
              "    return acc\n"),
         buggy=("def append_item(item, acc=[]):\n"
                "    acc.append(item)\n"
                "    return acc\n"),
         bug_line=1, bug_kind="mutable default argument",
         tests=[{"args": [1], "expected": [1]},
                {"args": [2, [9]], "expected": [9, 2]},
                {"args": ["a"], "expected": ["a"]},
                {"args": [0], "expected": [0]},
                {"args": [[1, 2]], "expected": [[1, 2]]},
                {"args": [5, []], "expected": [5]}]),
    dict(tier="medium", task_id="dedup", func="deduplicate",
         title="Order-preserving deduplication",
         ref=("def deduplicate(xs):\n"
              "    seen = set()\n"
              "    out = []\n"
              "    for x in xs:\n"
              "        if x not in seen:\n"
              "            seen.add(x)\n"
              "            out.append(x)\n"
              "    return out\n"),
         buggy=("def deduplicate(xs):\n"
                "    seen = set()\n"
                "    out = []\n"
                "    for x in xs:\n"
                "        if x in seen:\n"
                "            seen.add(x)\n"
                "            out.append(x)\n"
                "    return out\n"),
         bug_line=5, bug_kind="wrong operator (negation)",
         tests=[{"args": [[1, 2, 1, 3]], "expected": [1, 2, 3]},
                {"args": [[]], "expected": []},
                {"args": [[1, 1, 1]], "expected": [1]},
                {"args": [[3, 2, 1]], "expected": [3, 2, 1]},
                {"args": [["a", "b", "a"]], "expected": ["a", "b"]},
                {"args": [[1, 2, 3, 2, 1]] , "expected": [1, 2, 3]}]),
    dict(tier="medium", task_id="clamp", func="clamp",
         title="Clamp to range",
         ref=("def clamp(x, lo, hi):\n"
              "    return min(max(x, lo), hi)\n"),
         buggy=("def clamp(x, lo, hi):\n"
                "    return max(min(x, lo), hi)\n"),
         bug_line=2, bug_kind="wrong operator order",
         tests=[{"args": [5, 0, 10], "expected": 5},
                {"args": [-3, 0, 10], "expected": 0},
                {"args": [99, 0, 10], "expected": 10},
                {"args": [0, 0, 10], "expected": 0},
                {"args": [10, 0, 10], "expected": 10},
                {"args": [7, 7, 7], "expected": 7}]),
    dict(tier="hard", task_id="merge_sorted", func="merge_sorted",
         title="Merge two sorted lists",
         ref=("def merge_sorted(a, b):\n"
              "    i, j, out = 0, 0, []\n"
              "    while i < len(a) and j < len(b):\n"
              "        if a[i] <= b[j]:\n"
              "            out.append(a[i])\n"
              "            i += 1\n"
              "        else:\n"
              "            out.append(b[j])\n"
              "            j += 1\n"
              "    out.extend(a[i:])\n"
              "    out.extend(b[j:])\n"
              "    return out\n"),
         buggy=("def merge_sorted(a, b):\n"
                "    i, j, out = 0, 0, []\n"
                "    while i < len(a) and j < len(b):\n"
                "        if a[i] >= b[j]:\n"
                "            out.append(a[i])\n"
                "            i += 1\n"
                "        else:\n"
                "            out.append(b[j])\n"
                "            j += 1\n"
                "    out.extend(a[i:])\n"
                "    out.extend(b[j:])\n"
                "    return out\n"),
         bug_line=4, bug_kind="wrong comparator (flipped)",
         tests=[{"args": [[1, 3, 5], [2, 4, 6]], "expected": [1, 2, 3, 4, 5, 6]},
                {"args": [[], [1, 2]], "expected": [1, 2]},
                {"args": [[1, 2], []], "expected": [1, 2]},
                {"args": [[], []], "expected": []},
                {"args": [[1, 2, 2], [2, 3]], "expected": [1, 2, 2, 2, 3]},
                {"args": [[2, 2], [2]], "expected": [2, 2, 2]},
                {"args": [[5], [1]], "expected": [1, 5]}]),
    dict(tier="hard", task_id="prime", func="is_prime",
         title="Primality test",
         ref=("def is_prime(n):\n"
              "    if n < 2:\n"
              "        return False\n"
              "    r = int(n ** 0.5)\n"
              "    for d in range(2, r + 1):\n"
              "        if n % d == 0:\n"
              "            return False\n"
              "    return True\n"),
         buggy=("def is_prime(n):\n"
                "    if n < 2:\n"
                "        return False\n"
                "    r = int(n ** 0.5)\n"
                "    for d in range(2, r):\n"
                "        if n % d == 0:\n"
                "            return False\n"
                "    return True\n"),
         bug_line=5, bug_kind="off-by-one (missed divisor)",
         tests=[{"args": [2], "expected": True},
                {"args": [1], "expected": False},
                {"args": [0], "expected": False},
                {"args": [17], "expected": True},
                {"args": [49], "expected": False},
                {"args": [25], "expected": False},
                {"args": [97], "expected": True},
                {"args": [100], "expected": False}]),
    dict(tier="hard", task_id="gcd", func="gcd",
         title="Greatest common divisor",
         ref=("def gcd(a, b):\n"
              "    while b:\n"
              "        a, b = b, a % b\n"
              "    return a\n"),
         buggy=("def gcd(a, b):\n"
                "    while b:\n"
                "        a, b = b, a % b\n"
                "    return b\n"),
         bug_line=4, bug_kind="wrong variable returned",
         tests=[{"args": [12, 8], "expected": 4},
                {"args": [7, 5], "expected": 1},
                {"args": [0, 5], "expected": 5},
                {"args": [5, 0], "expected": 5},
                {"args": [100, 75], "expected": 25},
                {"args": [13, 13], "expected": 13}]),
    dict(tier="hard", task_id="movavg", func="moving_average",
         title="Moving average",
         ref=("def moving_average(nums, k):\n"
              "    out = []\n"
              "    window = sum(nums[:k])\n"
              "    out.append(window / k)\n"
              "    for i in range(k, len(nums)):\n"
              "        window += nums[i] - nums[i - k]\n"
              "        out.append(window / k)\n"
              "    return out\n"),
         buggy=("def moving_average(nums, k):\n"
                "    out = []\n"
                "    window = sum(nums[:k])\n"
                "    out.append(window / k)\n"
                "    for i in range(k, len(nums)):\n"
                "        window += nums[i] - nums[i - k + 1]\n"
                "        out.append(window / k)\n"
                "    return out\n"),
         bug_line=6, bug_kind="off-by-one index",
         tests=[{"args": [[1, 2, 3, 4, 5], 3], "expected": [2.0, 3.0, 4.0]},
                {"args": [[10, 20, 30], 3], "expected": [20.0]},
                {"args": [[5, 5, 5, 5], 2], "expected": [5.0, 5.0, 5.0]},
                {"args": [[1, 2, 3], 1], "expected": [1.0, 2.0, 3.0]},
                {"args": [[2, 4, 6, 8], 4], "expected": [5.0]},
                {"args": [[0, 10, 0, 10], 2], "expected": [5.0, 5.0, 5.0]}]),
]


def _def_params(code: str):
    """(func name, [param names without defaults]) from the def line."""
    import re as _re
    m = _re.match(r"\s*def\s+([A-Za-z_]\w*)\s*\(([^)]*)\)", code or "")
    assert m, (code.splitlines()[0] if code else code)
    names = []
    for part in m.group(2).split(","):
        part = part.strip()
        if part:
            names.append(part.split("=")[0].strip().lstrip("*"))
    return m.group(1), names


def _numbered(code: str) -> str:
    return "\n".join(f"{i + 1}: {line}" for i, line in enumerate(code.splitlines()))


def build_cases():
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for i, t in enumerate(BUGS):
        ref_out = pysandbox.run_function_tests(t["ref"], t["func"], t["tests"],
                                               timeout_s=5.0)
        assert ref_out["passed"] == ref_out["total"] == len(t["tests"]), \
            (t["task_id"], ref_out)
        # Signatures use the same meaningful parameter names as the spec:
        # ref and buggy agree on names (defaults may differ: the bug itself).
        assert _def_params(t["ref"]) == _def_params(t["buggy"]), t["task_id"]
        assert _def_params(t["ref"])[0] == t["func"], t["task_id"]
        bug_out = pysandbox.run_function_tests(t["buggy"], t["func"], t["tests"],
                                               timeout_s=5.0)
        failed = [k for k, r in enumerate(bug_out.get("results", []))
                  if not r.get("passed")]
        assert failed, (t["task_id"], "buggy code passes everything")
        # Special check: mutable-default bug only shows across calls; ensure
        # the visible failing test really fails standalone too, else fall back
        # to describing the cross-call failure explicitly.
        vis = t["tests"][failed[0]]
        numbered = _numbered(t["buggy"])
        assert t["buggy"].splitlines()[t["bug_line"] - 1] is not None
        prompt = (f"Task: {t['title']}\nThe function below contains a single bug "
                  f"({t['bug_kind']}). It fails this visible test:\n"
                  f"  {t['func']}({', '.join(repr(a) for a in vis['args'])}) "
                  f"should return {vis['expected']!r}.\n"
                  f"Buggy code (line numbers are for reference only, do not output them):\n"
                  f"{numbered}\n{REPAIR_SUFFIX}")
        by_tier[t["tier"]].append({
            "id": f"tmp-{i}",
            "test_id": TEST_ID,
            "tier": t["tier"],
            "lang": "en",
            "input": {"task_id": t["task_id"], "title": t["title"],
                      "func": t["func"], "buggy_numbered": numbered,
                      "visible_test": {"args": vis["args"],
                                       "expected": vis["expected"]},
                      "prompt": prompt},
            "expected": {"func": t["func"], "tests": t["tests"],
                         "bug_line": t["bug_line"], "reference": t["ref"]},
            "meta": {"bug_kind": t["bug_kind"]},
        })
    cases = interleave(by_tier["easy"], by_tier["medium"], by_tier["hard"])
    for j, c in enumerate(cases):
        c["id"] = f"HOME-06-{j + 1:02d}"
    return cases


def main() -> Path:
    out_dir = Path(__file__).resolve().parents[1] / "fixtures" / TEST_ID
    cases = build_cases()
    assert len(cases) == 12, len(cases)
    counts = {"easy": 0, "medium": 0, "hard": 0}
    for c in cases:
        counts[c["tier"]] += 1
    assert counts == {"easy": 4, "medium": 4, "hard": 4}, counts
    write_cases_and_manifest(out_dir, cases)
    return out_dir


if __name__ == "__main__":
    print(main())
