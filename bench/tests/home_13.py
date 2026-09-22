"""HOME-13 R0 word problems, numeric answers in \\boxed{} (owner: TASK_B1)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from bench.types import (
    Case, FORMAT_ERROR, OK, Profile, Request, Response, Verdict, WRONG_ANSWER,
)

META = dict(
    id="HOME-13",
    version="n1",
    title="Multi-step word problems, numeric answer in \\boxed{}",
    family="REASON",
    home="phi4-mini:latest",
    kind="chat",
    mode="R0",
    requires=["text"],
    num_predict=768,
    think_extra=4096,
    num_ctx=4096,
    timeout_s=300,
    core_n=10,
    empty_ok=False,
)

_BOXED_RE = re.compile(r"\\boxed\s*\{([^{}]*)\}")
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _parse_num(s: str):
    if s is None:
        return None
    t = s.strip().replace(",", "").replace(" ", "")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", t):
        return None
    try:
        return float(t)
    except Exception:
        return None


def _parse_boxed_last(text: str):
    found = _BOXED_RE.findall(text or "")
    if not found:
        return None
    return _parse_num(found[-1])


def _parse_bare_last(text: str):
    nums = _NUM_RE.findall(text or "")
    if not nums:
        return None
    return _parse_num(nums[-1])


def load_cases(fixtures_dir: str) -> list[Case]:
    path = Path(fixtures_dir) / "cases.jsonl"  # runner passes fixtures/HOME-13
    if not path.is_file():  # tolerate the fixtures root as well
        path = Path(fixtures_dir) / "HOME-13" / "cases.jsonl"
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
    exp = case.expected if isinstance(case.expected, dict) else {"answer": case.expected}
    expected = float(exp.get("answer"))
    tol = float(exp.get("tol", 1e-6))
    boxed = _parse_boxed_last(text)
    if boxed is not None:
        ok = abs(boxed - expected) <= tol
        return Verdict(
            status=OK if ok else WRONG_ANSWER,
            sub_reason=None if ok else "WRONG_VALUE",
            sem=1.0 if ok else 0.0,
            strict=1.0 if ok else 0.0,
            details={"parsed": boxed, "expected": expected, "tol": tol,
                     "boxed": True, "contract": "boxed"},
            attribution="MODEL" if not ok else "NONE",
        )
    bare = _parse_bare_last(text)
    if bare is not None:
        ok = abs(bare - expected) <= tol
        return Verdict(
            status=FORMAT_ERROR,
            sub_reason="BARE_NUMBER" if ok else "NO_BOXED",
            sem=1.0 if ok else 0.0,
            strict=0.0,
            details={"parsed": bare, "expected": expected, "tol": tol,
                     "boxed": False, "contract": "bare_number"},
            attribution="MODEL",
        )
    return Verdict(
        status=FORMAT_ERROR,
        sub_reason="NO_ANSWER",
        sem=0.0,
        strict=0.0,
        details={"parsed": None, "expected": expected, "tol": tol,
                 "boxed": False, "contract": "none"},
        attribution="MODEL",
    )
