"""Unit tests for TASK_B1 HOME test modules (validators + fixtures)."""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.types import Profile, Response

ROOT = Path(__file__).resolve().parents[1]
FIX = str(ROOT / "fixtures")


def _profile(tag="test-model", adapters=None):
    return Profile(tag=tag, kind="chat", caps=["text"], think="none",
                   ctx_max=8192, sampling={}, adapters=adapters or {})


def _resp(content):
    return Response(content=content)


def _load_cases(test_id):
    path = ROOT / "fixtures" / test_id / "cases.jsonl"
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


class _DictCase:
    def __init__(self, d):
        self.id = d["id"]
        self.input = d["input"]
        self.expected = d["expected"]


def test_home04_gold_prose_wrong_empty():
    from bench.tests import home_04
    cases = home_04.load_cases(FIX)
    assert len(cases) == 12
    case = cases[0]
    ans = case.expected["answer"]
    v = home_04.validate(case, _resp("\\boxed{%d}" % ans), _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0)
    v = home_04.validate(case, _resp("The answer is \\boxed{%d}." % ans), _profile())
    assert v.status == "OK" and v.sem == 1.0
    v = home_04.validate(case, _resp("After long reasoning the final number is %d" % ans),
                         _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0 and v.strict == 0.0
    v = home_04.validate(case, _resp("\\boxed{%d}" % (ans + 1)), _profile())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0
    v = home_04.validate(case, _resp(""), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0
    v = home_04.validate(case, _resp("no numbers here, just words"), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0


def test_home13_gold_and_variants():
    from bench.tests import home_13
    cases = home_13.load_cases(FIX)
    assert len(cases) == 20
    case = next(c for c in cases if c.expected.get("tol") == 0.01)
    ans = case.expected["answer"]
    v = home_13.validate(case, _resp("Result: \\boxed{%.2f}" % ans), _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0)
    v = home_13.validate(case, _resp("\\boxed{%.2f}" % (ans + 5.0)), _profile())
    assert v.status == "WRONG_ANSWER"
    v = home_13.validate(case, _resp("it is %.2f dollars" % ans), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0
    v = home_13.validate(case, _resp(""), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0


def test_home17_gold_wrong_malformed():
    from bench.tests import home_17
    cases = home_17.load_cases(FIX)
    assert len(cases) == 6
    case = cases[0]
    gold = json.loads(open(ROOT / "fixtures" / "HOME-17" / "cases.jsonl",
                           encoding="utf-8").read().splitlines()[0])["meta"]["gold"]
    raw = [json.loads(line) for line in
           open(ROOT / "fixtures" / "HOME-17" / "cases.jsonl", encoding="utf-8")]
    by_id = {d["id"]: d for d in raw}
    gold = by_id[case.id]["meta"]["gold"]
    v = home_17.validate(case, _resp(json.dumps(gold)), _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0), v.details
    v = home_17.validate(case, _resp("```json\n" + json.dumps(gold) + "\n```"), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0 and v.strict == 0.0
    v = home_17.validate(case, _resp("not json at all"), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0
    # Constraint-violating variant: drop one chosen element / remap one job.
    exp = case.expected
    if exp["kind"] == "select":
        bad = {"chosen": gold["chosen"][:-1]}
    elif exp["kind"] == "assign":
        bad = {"assignment": dict(gold["assignment"])}
        people = list(bad["assignment"])
        bad["assignment"][people[0]], bad["assignment"][people[1]] = \
            bad["assignment"][people[1]], bad["assignment"][people[0]]
    else:
        bad = {"machine": dict(gold["machine"]), "start": dict(gold["start"])}
        j = next(iter(bad["start"]))
        bad["start"][j] = 999
    v = home_17.validate(case, _resp(json.dumps(bad)), _profile())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0


def test_home14_gold_and_variants():
    from bench.tests import home_14
    cases = home_14.load_cases(FIX)
    assert len(cases) == 16
    case = next(c for c in cases if c.input.get("task_id") == "norm_spaces")
    ref = case.expected["reference"]
    v = home_14.validate(case, _resp("```python\n" + ref + "```"), _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0), v.details
    v = home_14.validate(case, _resp("Here is my solution:\n```python\n" + ref
                                     + "```\nHope this helps."), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0
    bad = ref.replace("join", "祝join") if "join" in ref else "def normalize_spaces(s):\n return 42\n"
    v = home_14.validate(case, _resp("```python\n" + bad + "```"), _profile())
    assert v.status in ("WRONG_ANSWER", "FORMAT_ERROR") and v.sem < 1.0
    v = home_14.validate(case, _resp("I do not know."), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0


def test_home06_gold_and_variants():
    from bench.tests import home_06
    cases = home_06.load_cases(FIX)
    assert len(cases) == 12
    case = next(c for c in cases if c.input.get("task_id") == "sum_range")
    ref = case.expected["reference"]
    line = case.expected["bug_line"]
    v = home_06.validate(case, _resp("```python\n" + ref + "```\nBUG_LINE: %d" % line),
                         _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0), v.details
    assert v.details["bug_line"]["correct"]
    v = home_06.validate(case, _resp("```python\n" + ref + "```\nBUG_LINE: %d" % (line + 1)),
                         _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0
    assert not v.details["bug_line"]["correct"]
    v = home_06.validate(case, _resp("```python\n" + ref + "```"), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0
    v = home_06.validate(case, _resp("no code here\nBUG_LINE: 1"), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0


def test_home20_gold_and_variants():
    from bench.tests import home_20
    cases = home_20.load_cases(FIX)
    assert len(cases) == 20
    raw = [json.loads(line) for line in
           open(ROOT / "fixtures" / "HOME-20" / "cases.jsonl", encoding="utf-8")]
    by_id = {d["id"]: d for d in raw}
    case = cases[0]
    gold_sql = by_id[case.id]["expected"]["gold_sql"]
    v = home_20.validate(case, _resp(gold_sql), _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0), v.details
    v = home_20.validate(case, _resp("The query is:\n```sql\n" + gold_sql + "\n```"),
                         _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0
    v = home_20.validate(case, _resp("SELECT name FROM customers WHERE 1 = 0"), _profile())
    assert v.status == "WRONG_ANSWER" and v.sem < 1.0
    v = home_20.validate(case, _resp("hello world"), _profile())
    assert v.status in ("FORMAT_ERROR", "WRONG_ANSWER")
    # Postgres-only syntax -> DIALECT_ERROR.
    v = home_20.validate(case, _resp("SELECT name::text FROM customers"), _profile())
    assert v.status == "WRONG_ANSWER" and v.sub_reason == "DIALECT_ERROR"


def test_home20_sqlcoder_raw_request():
    from bench.tests import home_20
    cases = home_20.load_cases(FIX)
    prof = _profile(tag="sqlcoder:7b", adapters={"sqlcoder_raw": True})
    req = home_20.build_request(cases[0], prof)
    assert req.endpoint == "generate" and req.raw is True
    assert "```sql" in (req.prompt or "")
    prof2 = _profile(tag="llama3.1:8b")
    req2 = home_20.build_request(cases[0], prof2)
    assert req2.endpoint == "chat"


def test_meta_values_match_spec():
    from bench.tests import (home_04, home_06, home_13, home_14, home_17,
                             home_20)
    expect = {
        "home_04": ("HOME-04", "deepseek-r1:8b", "REASON", "chat", "R1", 8192, 0, 10240, 900, 6),
        "home_06": ("HOME-06", "granite-code:8b-instruct", "CODE", "chat", "R1", 1024, 2048, 4096, 300, 8),
        "home_13": ("HOME-13", "phi4-mini:latest", "REASON", "chat", "R0", 768, 4096, 4096, 300, 10),
        "home_14": ("HOME-14", "qwen2.5-coder:7b", "CODE", "chat", "R1", 1536, 2048, 4096, 300, 8),
        "home_17": ("HOME-17", "qwen3:14b", "REASON", "chat", "R1", 6144, 0, 8192, 1200, 4),
        "home_20": ("HOME-20", "sqlcoder:7b", "SQL", "chat", "R0", 384, 1024, 4096, 120, 12),
    }
    mods = {"home_04": home_04, "home_06": home_06, "home_13": home_13,
            "home_14": home_14, "home_17": home_17, "home_20": home_20}
    for name, (i, h, fam, kind, mode, np, te, nc, to, cn) in expect.items():
        m = mods[name].META
        assert m["id"] == i, name
        assert m["home"] == h, name
        assert m["family"] == fam, name
        assert m["kind"] == kind, name
        assert m["mode"] == mode, name
        assert m["num_predict"] == np, name
        assert m["think_extra"] == te, name
        assert m["num_ctx"] == nc, name
        assert m["timeout_s"] == to, name
        assert m["core_n"] == cn, name


def _raw_cases(test_id):
    return [json.loads(line) for line in
            open(ROOT / "fixtures" / test_id / "cases.jsonl",
                 encoding="utf-8") if line.strip()]


def _case_by_question(mod, needle):
    for c in mod.load_cases(FIX):
        if needle in (c.input.get("question") or ""):
            return c
    raise AssertionError("no case with %r" % needle)


def test_home20_order_required_only_when_explicit():
    from gen.gen_home_20 import asks_order
    raw = _raw_cases("HOME-20")
    assert len(raw) == 20
    n_true = sum(1 for d in raw if d["expected"]["order_required"])
    for d in raw:
        assert (d["expected"]["order_required"]
                == asks_order(d["input"]["question"])), d["id"]
    assert n_true == 5


def test_home20_unordered_correct_and_ordered_strict():
    from bench.tests import home_20
    # Order-insensitive question: reversed row order is still OK.
    case = _case_by_question(home_20, "including employees without a department")
    raw = {d["id"]: d for d in _raw_cases("HOME-20")}
    gold = raw[case.id]["expected"]["gold_sql"]
    assert raw[case.id]["expected"]["order_required"] is False
    rev = gold.replace("ORDER BY e.name", "ORDER BY e.name DESC")
    assert rev != gold
    v = home_20.validate(case, _resp(rev), _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0), v.details
    # Order-sensitive question: reversed row order is wrong.
    ocase = _case_by_question(home_20, "ordered by id")
    oraw = {d["id"]: d for d in _raw_cases("HOME-20")}
    ogold = oraw[ocase.id]["expected"]["gold_sql"]
    assert oraw[ocase.id]["expected"]["order_required"] is True
    orev = ogold.replace("ORDER BY id", "ORDER BY id DESC")
    assert orev != ogold
    v = home_20.validate(ocase, _resp(orev), _profile())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0, v.details


def _swap_first_two_select_items(sql):
    m = re.match(r"(?is)^\s*select\s+(.*?)\s+from\s+(.*)$", sql)
    assert m, sql
    sel, rest = m.group(1), m.group(2)
    parts, depth, cur = [], 0, ""
    for ch in sel:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    assert len(parts) >= 2, sql
    parts[0], parts[1] = parts[1], parts[0]
    return "SELECT " + ", ".join(p.strip() for p in parts) + " FROM " + rest


def test_home20_permuted_columns_correct():
    from bench.tests import home_20
    case = _case_by_question(home_20, "including employees without a department")
    raw = {d["id"]: d for d in _raw_cases("HOME-20")}
    gold = raw[case.id]["expected"]["gold_sql"]
    swapped = _swap_first_two_select_items(gold)
    assert swapped != gold
    v = home_20.validate(case, _resp(swapped), _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0), v.details
    assert v.details.get("column_permutation") is True


def test_home20_extra_column_wrong():
    from bench.tests import home_20
    case = _case_by_question(home_20, "Customers with no referrer")
    raw = {d["id"]: d for d in _raw_cases("HOME-20")}
    gold = raw[case.id]["expected"]["gold_sql"]
    assert raw[case.id]["expected"]["order_required"] is False
    wide = gold.replace("SELECT name FROM", "SELECT name, id FROM")
    assert wide != gold
    v = home_20.validate(case, _resp(wide), _profile())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0, v.details
    assert v.details.get("column_permutation") is False


def test_home04_grid_convention():
    from bench.tests import home_04
    cases = home_04.load_cases(FIX)
    grids = [c for c in cases if c.input.get("kind") == "_lattice"]
    assert len(grids) >= 1
    for c in grids:
        p = c.input.get("prompt", "")
        assert "0-indexed" in p, c.id
        assert "row 0 is the top row" in p, c.id
        assert "column 0 is the leftmost" in p, c.id
        assert "(row, column)" in p, c.id


def test_home04_hard_upgrades():
    raw = {d["id"]: d for d in _raw_cases("HOME-04")}
    hard = [d for d in raw.values() if d["tier"] == "hard"]
    assert len(hard) == 4
    by_kind = {d["input"]["kind"]: d for d in hard}
    # 7x7 grid with 5 blocked cells.
    lat = by_kind["_lattice"]
    assert "7x7" in lat["input"]["prompt"]
    assert len(re.findall(r"\(\d+,\d+\)", lat["input"]["prompt"])) == 5
    # CRT with 4 moduli.
    mod = by_kind["_modular"]
    assert len(re.findall(r"x mod \d+ =", mod["input"]["prompt"])) == 4
    # Inclusion-exclusion counting over 1..10^5 (third verification here).
    ie = by_kind["_incexc"]
    assert "100000" in ie["input"]["prompt"]
    m = re.search(r"at least one of ([\d, ]+)\?", ie["input"]["prompt"])
    divs = [int(x) for x in m.group(1).split(",")]
    assert len(divs) >= 3
    expect = sum(1 for n in range(1, 100001) if any(n % d == 0 for d in divs))
    assert expect == ie["expected"]["answer"] > 0
    # Committees with two constraints.
    sel = by_kind["_select"]
    assert sel["input"]["prompt"].count("refuse to serve together") == 2
    assert "must be person" in sel["input"]["prompt"]


def test_home04_prob_three_draws_branch():
    import random
    from fractions import Fraction
    from gen.gen_home_04 import _prob
    prompt, ans = _prob(random.Random(0), "hard")
    assert "Three balls" in prompt
    same = 10 + 4 + 1 + 1  # C(5,3) + C(4,3) + C(3,3) + C(3,3)
    fr = Fraction(same, 455)  # C(15,3) triples
    assert ans == fr.numerator + fr.denominator == 471


def test_home14_signatures_meaningful():
    raw = _raw_cases("HOME-14")
    assert len(raw) == 16
    want = {
        "norm_spaces": "def normalize_spaces(s):",
        "sum_sq_even": "def sum_sq_even(nums):",
        "swmax": "def sliding_max(nums, k):",
    }
    seen = set()
    for d in raw:
        sig = d["input"]["signature"]
        ref_first = d["expected"]["reference"].splitlines()[0].strip()
        assert sig == ref_first, d["id"]
        assert ("Signature: " + sig) in d["input"]["prompt"], d["id"]
        # Hidden tests stay positional (args lists only).
        for tc in d["expected"]["tests"]:
            assert set(tc) == {"args", "expected"}, d["id"]
        tid = d["input"]["task_id"]
        seen.add(tid)
        if tid in want:
            assert sig == want[tid], d["id"]
    assert set(want) <= seen


def test_home06_param_names_consistent():
    raw = _raw_cases("HOME-06")
    assert len(raw) == 12

    def _params(code):
        m = re.match(r"\s*def\s+(\w+)\s*\(([^)]*)\)", code)
        assert m, code.splitlines()[0]
        names = [p.strip().split("=")[0].strip().lstrip("*")
                 for p in m.group(2).split(",") if p.strip()]
        return m.group(1), names

    for d in raw:
        ref = d["expected"]["reference"]
        buggy = d["input"]["buggy_numbered"]
        code = "\n".join(line.split(": ", 1)[1] for line in buggy.splitlines())
        assert _params(ref) == _params(code), d["id"]
        assert _params(ref)[0] == d["expected"]["func"], d["id"]
