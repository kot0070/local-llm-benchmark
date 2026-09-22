"""HOME-14 code generation, hidden tests in sandbox (owner: TASK_B1)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from bench.types import (
    Case, FORMAT_ERROR, OK, Profile, Request, Response, Verdict, WRONG_ANSWER,
)
from bench.validate import pysandbox

META = dict(
    id="HOME-14",
    version="n1",
    title="Code generation from spec, hidden tests",
    family="CODE",
    home="qwen2.5-coder:7b",
    kind="chat",
    mode="R1",
    requires=["text"],
    num_predict=1536,
    think_extra=2048,
    num_ctx=4096,
    timeout_s=300,
    core_n=8,
    empty_ok=False,
)

_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code(text: str, func: str) -> tuple[str | None, dict]:
    """Extract candidate code. Contract: one ```python block or raw code."""
    info = {"fenced": False, "prose": False, "strict": False}
    s = text or ""
    if not s.strip():
        return None, info
    fences = [b for b in _FENCE_RE.findall(s) if b.strip()]
    if fences:
        info["fenced"] = True
        outside = _FENCE_RE.sub("", s).strip()
        info["prose"] = bool(outside) or len(fences) > 1
        info["strict"] = (len(fences) == 1 and not outside)
        code = fences[0] if len(fences) == 1 else max(fences, key=len)
        return code.strip(), info
    # Raw code path: whole text must compile and define the function.
    try:
        compile(s, "<resp>", "exec")
        if re.search(r"(?m)^\s*def\s+" + re.escape(func) + r"\b", s):
            info["strict"] = True
            return s.strip(), info
    except Exception:
        pass
    m = re.search(r"(?m)^\s*def\s+" + re.escape(func) + r"\b", s)
    if m:
        info["prose"] = True
        return s[m.start():].strip(), info
    return None, info


def load_cases(fixtures_dir: str) -> list[Case]:
    path = Path(fixtures_dir) / "cases.jsonl"  # runner passes fixtures/HOME-14
    if not path.is_file():  # tolerate the fixtures root as well
        path = Path(fixtures_dir) / "HOME-14" / "cases.jsonl"
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


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    text = resp.content or ""
    exp = case.expected if isinstance(case.expected, dict) else {}
    func = exp.get("func", "")
    tests = exp.get("tests", [])
    code, info = extract_code(text, func)
    if code is None:
        return Verdict(status=FORMAT_ERROR, sub_reason="NO_CODE", sem=0.0,
                       strict=0.0,
                       details={"passed": 0, "total": len(tests), "failures": [],
                                "fenced": info["fenced"], "prose": info["prose"]},
                       attribution="MODEL")
    try:
        compile(code, "<candidate>", "exec")
    except Exception as e:
        return Verdict(status=WRONG_ANSWER, sub_reason="COMPILE_ERROR", sem=0.0,
                       strict=0.0,
                       details={"passed": 0, "total": len(tests),
                                "failures": [{"error": "COMPILE: %s" % e}],
                                "fenced": info["fenced"], "prose": info["prose"]},
                       attribution="MODEL")
    out = pysandbox.run_function_tests(code, func, tests, timeout_s=5.0)
    if out.get("error") and not out.get("results"):
        return Verdict(status=WRONG_ANSWER, sub_reason="SANDBOX_SETUP_FAIL",
                       sem=0.0, strict=0.0,
                       details={"passed": 0, "total": len(tests),
                                "failures": [{"error": out.get("error")}],
                                "fenced": info["fenced"], "prose": info["prose"]},
                       attribution="MODEL")
    passed = out.get("passed", 0)
    total = out.get("total", len(tests)) or len(tests)
    sem = (passed / total) if total else 0.0
    failures = [{"index": i, "error": r.get("error"), "got": r.get("got"),
                 "expected": r.get("expected")}
                for i, r in enumerate(out.get("results", [])) if not r.get("passed")][:5]
    if passed == total and total > 0:
        if info["prose"]:
            return Verdict(status=FORMAT_ERROR, sub_reason="PROSE_AROUND_CODE",
                           sem=1.0, strict=0.0,
                           details={"passed": passed, "total": total,
                                    "failures": [], "fenced": info["fenced"],
                                    "prose": True}, attribution="MODEL")
        return Verdict(status=OK, sub_reason=None, sem=1.0, strict=1.0,
                       details={"passed": passed, "total": total, "failures": [],
                                "fenced": info["fenced"], "prose": False},
                       attribution="NONE")
    if info["prose"]:
        return Verdict(status=FORMAT_ERROR, sub_reason="PROSE_AROUND_CODE",
                       sem=sem, strict=0.0,
                       details={"passed": passed, "total": total,
                                "failures": failures, "fenced": info["fenced"],
                                "prose": True}, attribution="MODEL")
    return Verdict(status=WRONG_ANSWER, sub_reason="TESTS_FAILED", sem=sem,
                   strict=0.0,
                   details={"passed": passed, "total": total,
                            "failures": failures, "fenced": info["fenced"],
                            "prose": False}, attribution="MODEL")
