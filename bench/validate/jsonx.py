"""Shared JSON helpers for BENCH V5 NIGHT-1 (owner: TASK_B1).

Implements exactly the API in SPEC_NIGHT.md "Shared cross-module APIs".
Stdlib only.
"""
from __future__ import annotations

import json


def extract_json(text: str) -> tuple[object | None, dict]:
    """Extract one JSON value from free-form model output.

    Returns (obj_or_None, info) where info =
    {"strict": bool, "lenient": bool, "fenced": bool, "prose": bool}.

    strict  = whole stripped text is one JSON value.
    lenient = first JSON object/array found after removing ``` fences / prose.
    fenced  = triple-backtick fences were present.
    prose   = there was extra text around the parsed JSON value.
    """
    info = {"strict": False, "lenient": False, "fenced": False, "prose": False}
    if text is None:
        return None, info
    s = text.strip()
    if not s:
        return None, info
    info["fenced"] = "```" in s

    # Strict: the whole stripped text parses as one JSON value.
    try:
        obj = json.loads(s)
        info["strict"] = True
        info["lenient"] = True
        info["prose"] = False
        return obj, info
    except Exception:
        pass

    # Collect candidate substrings: contents of fenced blocks first,
    # then the text with fences stripped.
    candidates: list[str] = []
    tmp = s
    while True:
        start = tmp.find("```")
        if start == -1:
            break
        end = tmp.find("```", start + 3)
        if end == -1:
            block = tmp[start + 3:]
            tmp = ""
        else:
            block = tmp[start + 3:end]
            tmp = tmp[:start] + "\n" + tmp[end + 3:]
        # Drop an optional language tag on the first line (e.g. ```json).
        lines = block.split("\n", 1)
        if len(lines) == 2 and lines[0].strip().isalpha():
            block = lines[1]
        candidates.append(block.strip())
    candidates.append(tmp.strip())
    candidates.append(s)

    for cand in candidates:
        if not cand:
            continue
        # Try whole-candidate parse first.
        try:
            obj = json.loads(cand)
            info["lenient"] = True
            info["prose"] = True
            return obj, info
        except Exception:
            pass
        # Scan for the first JSON object/array via raw_decode.
        decoder = json.JSONDecoder()
        for i, ch in enumerate(cand):
            if ch not in "{[":
                continue
            try:
                obj, endpos = decoder.raw_decode(cand[i:])
                if isinstance(obj, (dict, list)):
                    info["lenient"] = True
                    info["prose"] = True
                    return obj, info
            except Exception:
                continue
    return None, info


def _norm_date(s: str) -> str:
    t = s.strip().lower().replace("/", "-").replace(".", "-").replace("_", "-")
    # Keep only digits and separators, collapse repeats.
    out = []
    for ch in t:
        if ch.isdigit() or ch == "-" or ch == ":" or ch in ("t", " ", "z"):
            out.append(ch)
    t = "".join(out).strip("-")
    # Compare on the date part only (first 10 chars normalised to numbers).
    import re

    m = re.search(r"(\d{1,4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        y, mo, d = (int(x) for x in m.groups())
        return f"{y:04d}-{mo:02d}-{d:02d}"
    nums = re.findall(r"\d+", t)
    if nums:
        return "-".join(nums)
    return s.strip().lower()


def _canon(x):
    if isinstance(x, float):
        return f"f:{x!r}"
    if isinstance(x, bool):
        return f"b:{x!r}"
    if x is None:
        return "n:null"
    try:
        return "j:" + json.dumps(x, sort_keys=True, ensure_ascii=False)
    except Exception:
        return "s:" + str(x)


def _field_score(got, exp, kind: str) -> tuple[float, dict]:
    detail: dict = {"kind": kind, "got": got, "expected": exp}
    if kind == "exact":
        s = 1.0 if got == exp else 0.0
        # bool is subclass of int: require identical type for exactness.
        if isinstance(got, bool) != isinstance(exp, bool):
            s = 0.0
        detail["score"] = s
        return s, detail
    if kind == "ci":
        s = 1.0 if str(got).strip().casefold() == str(exp).strip().casefold() else 0.0
        detail["score"] = s
        return s, detail
    if kind == "num":
        try:
            s = 1.0 if abs(float(got) - float(exp)) <= 1e-6 else 0.0
        except Exception:
            s = 0.0
        detail["score"] = s
        return s, detail
    if kind.startswith("num_tol:"):
        try:
            tol = float(kind.split(":", 1)[1])
        except Exception:
            tol = 0.0
        try:
            s = 1.0 if abs(float(got) - float(exp)) <= tol else 0.0
        except Exception:
            s = 0.0
        detail["score"] = s
        detail["tol"] = tol
        return s, detail
    if kind == "date":
        s = 1.0 if _norm_date(str(got)) == _norm_date(str(exp)) else 0.0
        detail["score"] = s
        detail["norm_got"] = _norm_date(str(got))
        detail["norm_expected"] = _norm_date(str(exp))
        return s, detail
    if kind in ("set", "set_ci"):
        gl = got if isinstance(got, list) else [got]
        el = exp if isinstance(exp, list) else [exp]
        if kind == "set_ci":
            gs = {str(x).strip().casefold() for x in gl}
            es = {str(x).strip().casefold() for x in el}
        else:
            gs = {_canon(x) for x in gl}
            es = {_canon(x) for x in el}
        if not gs and not es:
            detail["score"] = 1.0
            return 1.0, detail
        inter = len(gs & es)
        union = len(gs | es)
        s = (inter / union) if union else 0.0
        detail["score"] = s
        detail["intersection"] = inter
        detail["union"] = union
        return s, detail
    if kind == "null":
        s = 1.0 if got is None else 0.0
        detail["score"] = s
        return s, detail
    detail["score"] = 0.0
    detail["error"] = f"unknown spec kind {kind!r}"
    return 0.0, detail


def compare_fields(got, expected: dict, spec: dict) -> tuple[float, dict]:
    """Compare dict fields per spec; missing field scores 0.

    spec[field] in {"exact","ci","num","num_tol:<x>","date","set","set_ci","null"}.
    Returns (mean field score, per-field detail).
    """
    got = got if isinstance(got, dict) else {}
    expected = expected if isinstance(expected, dict) else {}
    spec = spec if isinstance(spec, dict) else {}
    keys = list(spec.keys()) or list(expected.keys())
    if not keys:
        return 1.0, {}
    details: dict = {}
    scores: list[float] = []
    for k in keys:
        kind = spec.get(k, "exact")
        exp = expected.get(k)
        if not isinstance(got, dict) or k not in got:
            details[k] = {"kind": kind, "got": None, "expected": exp,
                          "score": 0.0, "missing": True}
            scores.append(0.0)
            continue
        s, d = _field_score(got[k], exp, kind)
        details[k] = d
        scores.append(s)
    return (sum(scores) / len(scores)) if scores else 1.0, details
