"""Tool-call helpers for BENCH V5 NIGHT-1 (owner: TASK_C).

Implements exactly the SPEC shared API:
  normalize_calls(resp) -> (calls, channel)
  args_equal(got, exp, schema) -> (equal, detail)
Stdlib only.
"""
from __future__ import annotations

import json


def _coerce_args(args):
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        s = args.strip()
        if not s:
            return {}
        try:
            v = json.loads(s)
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}
    return {}


def _normalize_one(tc) -> dict | None:
    if not isinstance(tc, dict):
        return None
    name = None
    args = {}
    if isinstance(tc.get("function"), dict):
        fn = tc["function"]
        name = fn.get("name", fn.get("tool", fn.get("function", "")))
        if "arguments" in fn:
            args = fn["arguments"]
        elif "parameters" in fn:
            args = fn["parameters"]
        elif "args" in fn:
            args = fn["args"]
        else:
            args = {}
    else:
        name = tc.get("name", tc.get("function", tc.get("tool", tc.get("id", ""))))
        if "arguments" in tc:
            args = tc["arguments"]
        elif "parameters" in tc:
            args = tc["parameters"]
        elif "args" in tc:
            args = tc["args"]
        else:
            args = {}
        # {"function": "name-string", "arguments": {...}} variant
        if not isinstance(name, str) or not name:
            f = tc.get("function", "")
            if isinstance(f, str) and f:
                name = f
    if not isinstance(name, str) or not name.strip():
        return None
    args = _coerce_args(args)
    if not isinstance(args, dict):
        args = {}
    return {"name": name.strip(), "arguments": args}


def _scan_textual(content: str) -> list[dict]:
    out: list[dict] = []
    if not isinstance(content, str) or not content.strip():
        return out
    s = content
    # Remove triple-backtick fences but keep their inner content for scanning.
    # We scan both the full text and fence interiors; dedupe by span is not
    # needed since we scan sequentially with raw_decode.
    decoder = json.JSONDecoder()
    i = 0
    n = len(s)
    seen_spans = []
    while i < n:
        ch = s[i]
        if ch not in "{[":
            i += 1
            continue
        try:
            obj, end = decoder.raw_decode(s[i:])
        except Exception:
            i += 1
            continue
        # Only consider dict objects as candidate calls.
        if isinstance(obj, dict):
            cand = _normalize_one(obj)
            # Require explicit tool-call shape: name + arguments/parameters keys.
            if cand is not None and ("arguments" in obj or "parameters" in obj or "args" in obj or isinstance(obj.get("function"), dict)):
                # Avoid trivial {"name": ...} without args keys unless it has function dict.
                out.append(cand)
                seen_spans.append((i, i + end))
        # Advance past this value to find further calls.
        if end and end > 0:
            i = i + max(1, end)
        else:
            i += 1
    return out


def normalize_calls(resp) -> tuple[list[dict], str]:
    """Normalize tool calls from a Response.

    Returns ([{"name","arguments": dict}], channel) where channel is
    "native" | "textual" | "none".
    Textual = JSON objects with name+arguments (or function/parameters)
    found in content when the native list is empty.
    """
    native_raw = getattr(resp, "tool_calls", None) or []
    content = getattr(resp, "content", "") or ""
    calls: list[dict] = []
    for tc in native_raw:
        c = _normalize_one(tc)
        if c is not None:
            calls.append(c)
    if calls:
        return calls, "native"
    textual = _scan_textual(content if isinstance(content, str) else str(content))
    if textual:
        return textual, "textual"
    return [], "none"


def _is_bool(x) -> bool:
    return isinstance(x, bool)


def _num_equal(a, b) -> bool:
    # Bool is never numerically equal to numbers.
    if _is_bool(a) or _is_bool(b):
        return a is b
    try:
        fa = float(a)
        fb = float(b)
    except Exception:
        return False
    return abs(fa - fb) <= 1e-6


def _str_equal(got, exp, detail_flag: dict) -> bool:
    if not isinstance(got, str) or not isinstance(exp, str):
        return got == exp
    gs = got.strip()
    es = exp.strip()
    if gs == es:
        if got != exp:
            detail_flag["whitespace_padded"] = True
        return True
    return False


def _value_equal(got, exp, subschema, detail_flag: dict) -> bool:
    # Bool strictness first.
    if _is_bool(got) or _is_bool(exp):
        return got is exp
    stype = ""
    if isinstance(subschema, dict):
        stype = str(subschema.get("type", "")).lower()
    if stype in ("integer", "number"):
        return _num_equal(got, exp)
    if isinstance(got, str) and isinstance(exp, str):
        return _str_equal(got, exp, detail_flag)
    # Numeric equivalence even without schema (5 vs 5.0).
    if isinstance(got, (int, float)) and isinstance(exp, (int, float)):
        return _num_equal(got, exp)
    # Numeric strings vs numbers: allow "5" == 5.
    if isinstance(got, (int, float, str)) and isinstance(exp, (int, float, str)):
        try:
            # Only coerce if both look numeric.
            float(str(got).strip())
            float(str(exp).strip())
            # If both parse, compare numerically (covers "5" vs 5).
            if stype in ("", "integer", "number", "string"):
                # For plain strings that are numeric, numeric compare is fine.
                # But avoid coercing non-numeric strings (float() raises -> False path).
                return _num_equal(str(got).strip(), str(exp).strip())
        except Exception:
            pass
    if isinstance(got, dict) and isinstance(exp, dict):
        props = subschema.get("properties", {}) if isinstance(subschema, dict) else {}
        if set(got.keys()) != set(exp.keys()):
            return False
        for k in got:
            if not _value_equal(got[k], exp[k], props.get(k) if isinstance(props, dict) else None, detail_flag):
                return False
        return True
    if isinstance(got, list) and isinstance(exp, list):
        if len(got) != len(exp):
            return False
        items_schema = subschema.get("items") if isinstance(subschema, dict) else None
        sub = items_schema if isinstance(items_schema, dict) else None
        for a, b in zip(got, exp):
            if not _value_equal(a, b, sub, detail_flag):
                return False
        return True
    return got == exp


def args_equal(got: dict, exp: dict, schema: dict | None) -> tuple[bool, dict]:
    """Compare tool arguments per JSON-schema types.

    Number/integer equivalence per schema type, whitespace-stripped strings
    (flag whitespace_padded), extra keys -> not equal.
    """
    got = got if isinstance(got, dict) else {}
    exp = exp if isinstance(exp, dict) else {}
    schema = schema if isinstance(schema, dict) else {}
    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    if not isinstance(props, dict):
        props = {}
    extra = sorted(set(got.keys()) - set(exp.keys()))
    missing = sorted(set(exp.keys()) - set(got.keys()))
    mismatched: list[str] = []
    per_field: dict = {}
    flag = {"whitespace_padded": False}
    for k in sorted(set(got.keys()) & set(exp.keys())):
        sub = props.get(k) if isinstance(props, dict) else None
        eq = _value_equal(got[k], exp[k], sub if isinstance(sub, dict) else None, flag)
        per_field[k] = {"equal": eq, "got": got[k], "expected": exp[k]}
        if not eq:
            mismatched.append(k)
    equal = (not extra) and (not missing) and (not mismatched)
    detail = {
        "equal": equal,
        "extra_keys": extra,
        "missing_keys": missing,
        "mismatched_keys": sorted(mismatched),
        "whitespace_padded": bool(flag["whitespace_padded"]),
        "per_field": per_field,
    }
    return equal, detail
