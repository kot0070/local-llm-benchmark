"""HOME-17 R1 constraint problems, JSON solution (owner: TASK_B1)."""
from __future__ import annotations

import json
from pathlib import Path

from bench.types import (
    Case, FORMAT_ERROR, OK, Profile, Request, Response, Verdict, WRONG_ANSWER,
)
from bench.validate.jsonx import extract_json

META = dict(
    id="HOME-17",
    version="n1",
    title="Constrained optimisation, JSON solution",
    family="REASON",
    home="qwen3:14b",
    kind="chat",
    mode="R1",
    requires=["text"],
    num_predict=6144,
    think_extra=0,
    num_ctx=8192,
    timeout_s=1200,
    core_n=4,
    empty_ok=False,
)


def load_cases(fixtures_dir: str) -> list[Case]:
    path = Path(fixtures_dir) / "cases.jsonl"  # runner passes fixtures/HOME-17
    if not path.is_file():  # tolerate the fixtures root as well
        path = Path(fixtures_dir) / "HOME-17" / "cases.jsonl"
    cases: list[Case] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cases.append(Case(id=d["id"], test_id=d["test_id"], tier=d.get("tier", ""),
                              lang=d.get("lang", "en"), input=d.get("input", {}),
                              expected=d.get("expected"), meta=d.get("meta", {})))
    return cases


def build_request(case: Case, profile: Profile) -> Request:
    prompt = case.input.get("prompt", "")
    return Request(endpoint="chat", messages=[{"role": "user", "content": prompt}])


def _check_schedule(got: dict, data: dict):
    violations: list[str] = []
    durations = {str(k): v for k, v in data["durations"].items()}
    jobs = list(durations)
    eligible = {str(k): list(v) for k, v in data.get("eligible", {}).items()}
    prec = [(str(a), str(b)) for a, b in data.get("precedences", [])]
    machine = got.get("machine") if isinstance(got, dict) else None
    start = got.get("start") if isinstance(got, dict) else None
    if not isinstance(machine, dict) or not isinstance(start, dict):
        return False, None, ["SOLUTION_MUST_HAVE_MACHINE_AND_START"]
    machine = {str(k): v for k, v in machine.items()}
    start = {str(k): v for k, v in start.items()}
    for j in jobs:
        if j not in machine or j not in start:
            violations.append(f"MISSING_JOB:{j}")
    if violations:
        return False, None, violations
    try:
        for j in jobs:
            m = int(machine[j])
            s = start[j]
            if not isinstance(s, (int, float)) or s < 0:
                violations.append(f"BAD_START:{j}")
            if m not in (0, 1):
                violations.append(f"BAD_MACHINE:{j}")
            if j in eligible and m not in eligible[j]:
                violations.append(f"INELIGIBLE:{j}->m{m}")
    except Exception:
        return False, None, violations + ["BAD_TYPES"]
    finish = {j: start[j] + durations[j] for j in jobs}
    for a, b in prec:
        if start[b] < finish[a]:
            violations.append(f"PRECEDENCE:{a}->{b}")
    for m in (0, 1):
        mine = sorted([j for j in jobs if int(machine[j]) == m], key=lambda j: start[j])
        for x, y in zip(mine, mine[1:]):
            if start[y] < finish[x]:
                violations.append(f"OVERLAP:m{m}:{x},{y}")
    if violations:
        return False, None, violations
    makespan = max(finish.values()) if finish else 0
    return True, makespan, []


def _check_assign(got: dict, data: dict):
    violations: list[str] = []
    people = list(data["people"])
    slots = list(data["slots"])
    scores = data["scores"]
    fixed = {str(k): str(v) for k, v in data.get("fixed", {}).items()}
    forbidden = [(str(a), str(b)) for a, b in data.get("forbidden", [])]
    asg = got.get("assignment") if isinstance(got, dict) else None
    if not isinstance(asg, dict):
        return False, None, ["SOLUTION_MUST_HAVE_ASSIGNMENT"]
    asg = {str(k): str(v) for k, v in asg.items()}
    if set(asg) != set(people):
        return False, None, ["MUST_ASSIGN_ALL_PEOPLE"]
    if sorted(asg.values()) != sorted(slots):
        violations.append("SLOTS_NOT_BIJECTION")
    for p, s in fixed.items():
        if asg.get(p) != s:
            violations.append(f"FIXED:{p}->{s}")
    for p, s in forbidden:
        if asg.get(p) == s:
            violations.append(f"FORBIDDEN:{p}->{s}")
    if violations:
        return False, None, violations
    try:
        total = sum(scores[p][s] for p, s in asg.items())
    except Exception:
        return False, None, ["BAD_SCORE_LOOKUP"]
    return True, total, []


def _check_select(got: dict, data: dict):
    violations: list[str] = []
    items = {str(i["id"]): i for i in data["items"]}
    budget = data["budget"]
    exclusions = [(str(a), str(b)) for a, b in data.get("exclusions", [])]
    required = [str(x) for x in data.get("required", [])]
    atleast = data.get("atleast") or {}
    chosen = got.get("chosen") if isinstance(got, dict) else None
    if not isinstance(chosen, list):
        return False, None, ["SOLUTION_MUST_HAVE_CHOSEN_LIST"]
    chosen = [str(x) for x in chosen]
    if len(set(chosen)) != len(chosen):
        violations.append("DUPLICATE_CHOICES")
    unknown = [x for x in chosen if x not in items]
    if unknown:
        return False, None, [f"UNKNOWN_ITEM:{x}" for x in unknown]
    cost = sum(items[x]["cost"] for x in chosen)
    if cost > budget:
        violations.append(f"OVER_BUDGET:{cost}>{budget}")
    for a, b in exclusions:
        if a in chosen and b in chosen:
            violations.append(f"EXCLUSION:{a},{b}")
    for r in required:
        if r not in chosen:
            violations.append(f"MISSING_REQUIRED:{r}")
    if atleast:
        group = [str(x) for x in atleast.get("group", [])]
        k = int(atleast.get("k", 0))
        if sum(1 for x in group if x in chosen) < k:
            violations.append("ATLEAST_NOT_MET")
    if violations:
        return False, None, violations
    value = sum(items[x]["value"] for x in chosen)
    return True, value, violations


def check_solution(kind: str, got: dict, data: dict):
    if kind == "schedule":
        return _check_schedule(got, data)
    if kind == "assign":
        return _check_assign(got, data)
    if kind == "select":
        return _check_select(got, data)
    return False, None, [f"UNKNOWN_KIND:{kind}"]


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    text = resp.content or ""
    exp = case.expected if isinstance(case.expected, dict) else {}
    kind = exp.get("kind", "")
    optimum = exp.get("optimum")
    data = exp.get("data", {})
    obj, info = extract_json(text)
    if not isinstance(obj, dict):
        return Verdict(
            status=FORMAT_ERROR,
            sub_reason="NO_JSON_OBJECT",
            sem=0.0,
            strict=0.0,
            details={"valid": False, "objective": None, "optimum": optimum,
                     "violations": ["NO_JSON_OBJECT"], "strict_json": info["strict"],
                     "lenient_json": info["lenient"]},
            attribution="MODEL",
        )
    valid, objective, violations = check_solution(kind, obj, data)
    contract_ok = bool(info["strict"])
    sem = 1.0 if (valid and objective == optimum) else 0.0
    if sem == 1.0 and contract_ok:
        return Verdict(status=OK, sub_reason=None, sem=1.0, strict=1.0,
                       details={"valid": True, "objective": objective,
                                "optimum": optimum, "violations": [],
                                "strict_json": True}, attribution="NONE")
    if sem == 1.0:
        return Verdict(status=FORMAT_ERROR, sub_reason="JSON_NOT_STRICT",
                       sem=1.0, strict=0.0,
                       details={"valid": True, "objective": objective,
                                "optimum": optimum, "violations": [],
                                "strict_json": False,
                                "lenient_json": info["lenient"],
                                "fenced": info["fenced"], "prose": info["prose"]},
                       attribution="MODEL")
    reason = "CONSTRAINT_VIOLATED" if not valid else "SUBOPTIMAL"
    return Verdict(status=WRONG_ANSWER, sub_reason=reason, sem=0.0, strict=0.0,
                   details={"valid": valid, "objective": objective,
                            "optimum": optimum, "violations": violations,
                            "strict_json": info["strict"]},
                   attribution="MODEL")
