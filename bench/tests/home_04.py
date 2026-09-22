"""HOME-04 R1 math with integer answers (owner: TASK_B1)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from bench.types import (
    Case, FORMAT_ERROR, OK, Profile, Request, Response, Verdict, WRONG_ANSWER,
)

META = dict(
    id="HOME-04",
    version="n1",
    title="Competition math, integer answer in \\boxed{}",
    family="REASON",
    home="deepseek-r1:8b",
    kind="chat",
    mode="R1",
    requires=["text"],
    num_predict=8192,  # SMOKE3: 11776 still truncated in thinking and forced offload (28 tok/s, 422 s/case)
    think_extra=0,
    num_ctx=10240,
    timeout_s=900,
    core_n=6,
    empty_ok=False,
)

_BOXED_RE = re.compile(r"\\boxed\s*\{([^{}]*)\}")
_INT_RE = re.compile(r"-?\d+")


def _parse_boxed_last(text: str):
    found = _BOXED_RE.findall(text or "")
    if not found:
        return None
    inner = found[-1].strip().replace(",", "").replace(" ", "")
    if re.fullmatch(r"-?\d+", inner):
        try:
            return int(inner)
        except Exception:
            return None
    return None


def _parse_bare_last(text: str):
    nums = _INT_RE.findall(text or "")
    if not nums:
        return None
    try:
        return int(nums[-1])
    except Exception:
        return None


def load_cases(fixtures_dir: str) -> list[Case]:
    path = Path(fixtures_dir) / "cases.jsonl"  # runner passes fixtures/HOME-04
    if not path.is_file():  # tolerate the fixtures root as well
        path = Path(fixtures_dir) / "HOME-04" / "cases.jsonl"
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
    expected = case.expected.get("answer") if isinstance(case.expected, dict) else case.expected
    boxed = _parse_boxed_last(text)
    if boxed is not None:
        ok = (boxed == expected)
        return Verdict(
            status=OK if ok else WRONG_ANSWER,
            sub_reason=None if ok else "WRONG_VALUE",
            sem=1.0 if ok else 0.0,
            strict=1.0 if ok else 0.0,
            details={"parsed": boxed, "expected": expected, "boxed": True,
                     "contract": "boxed"},
            attribution="MODEL" if not ok else "NONE",
        )
    bare = _parse_bare_last(text)
    if bare is not None:
        ok = (bare == expected)
        return Verdict(
            status=FORMAT_ERROR,
            sub_reason="BARE_INTEGER" if ok else "NO_BOXED",
            sem=1.0 if ok else 0.0,
            strict=0.0,
            details={"parsed": bare, "expected": expected, "boxed": False,
                     "contract": "bare_integer"},
            attribution="MODEL",
        )
    return Verdict(
        status=FORMAT_ERROR,
        sub_reason="NO_ANSWER",
        sem=0.0,
        strict=0.0,
        details={"parsed": None, "expected": expected, "boxed": False,
                 "contract": "none"},
        attribution="MODEL",
    )
