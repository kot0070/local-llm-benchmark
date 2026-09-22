"""HOME-22 vision+tools (home model qwen3.5:4b). Vision kind, single-turn tool call."""
from __future__ import annotations

import base64
import json
import os

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-22", version="n1", title="Vision tool calling", family="VISION_TOOLS",
            home="qwen3.5:4b", kind="vision", mode="R0", requires=["vision", "tools"],
            num_predict=256, think_extra=1024, num_ctx=12288, timeout_s=180, core_n=10, empty_ok=False)

TOOLS = [
    {"name": "submit_form", "description": "Submit a completed form",
     "parameters": {"type": "object", "properties": {"form_id": {"type": "string"}, "name": {"type": "string"}, "amount": {"type": "number"}}, "required": ["form_id", "name", "amount"]}},
    {"name": "open_ticket", "description": "Open a support ticket",
     "parameters": {"type": "object", "properties": {"subject": {"type": "string"}, "priority": {"type": "string"}}, "required": ["subject", "priority"]}},
    {"name": "ask_user", "description": "Ask the user for a missing required field",
     "parameters": {"type": "object", "properties": {"question": {"type": "string"}, "missing_field": {"type": "string"}}, "required": ["question", "missing_field"]}},
    {"name": "cancel_request", "description": "Cancel a pending request (mutation)",
     "parameters": {"type": "object", "properties": {"request_id": {"type": "string"}, "reason": {"type": "string"}}, "required": ["request_id", "reason"]}},
    {"name": "refund_payment", "description": "Refund a payment (mutation)",
     "parameters": {"type": "object", "properties": {"payment_id": {"type": "string"}, "amount": {"type": "number"}}, "required": ["payment_id", "amount"]}},
    {"name": "read_record", "description": "Read a stored record",
     "parameters": {"type": "object", "properties": {"record_id": {"type": "string"}}, "required": ["record_id"]}},
]

try:
    from bench.validate.toolsx import normalize_calls as _normalize, args_equal as _args_equal
except Exception:
    _normalize = _args_equal = None


def _local_normalize(resp):
    native = []
    for tc in (getattr(resp, "tool_calls", None) or []):
        if isinstance(tc, dict) and tc.get("name"):
            args = tc.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            native.append({"name": tc.get("name"), "arguments": args if isinstance(args, dict) else {}})
    if native:
        return native, "native"
    import re
    textual = []
    body = resp.content or ""
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", body, re.DOTALL | re.IGNORECASE)
    blobs = [m.group(1)] if m else [body]
    dec = json.JSONDecoder()
    for blob in blobs:
        for i, ch in enumerate(blob):
            if ch == "{":
                try:
                    v, _e = dec.raw_decode(blob[i:])
                except Exception:
                    continue
                if isinstance(v, dict):
                    name = v.get("name", v.get("function", v.get("tool")))
                    args = v.get("arguments", v.get("parameters", v.get("args", v.get("input"))))
                    if isinstance(name, str) and isinstance(args, dict):
                        textual.append({"name": name, "arguments": args})
                break
    if textual:
        return textual, "textual"
    return [], "none"


def _local_args_equal(got, exp, schema):
    if not isinstance(got, dict) or not isinstance(exp, dict):
        return False, {"reason": "non-dict"}
    props = (schema or {}).get("properties", {}) if isinstance(schema, dict) else {}
    detail, ok = {}, True
    for k, ev in exp.items():
        if k not in got:
            ok = False
            detail[k] = {"got": None, "expected": ev, "match": False, "reason": "missing"}
            continue
        gv = got[k]
        ptype = props.get(k, {}).get("type") if isinstance(props.get(k), dict) else None
        if ptype in ("number", "integer") or (isinstance(ev, (int, float)) and isinstance(gv, (int, float))):
            match = float(gv) == float(ev)
        elif isinstance(ev, str) and isinstance(gv, str):
            match = gv.strip() == ev.strip()
            detail[k] = {"match": match, "whitespace_padded": (match and gv != ev)}
            if not match:
                ok = False
            continue
        else:
            match = gv == ev
        detail[k] = {"got": gv, "expected": ev, "match": bool(match)}
        if not match:
            ok = False
    extra = [k for k in got if k not in exp]
    if extra:
        ok = False
        detail["extra_keys"] = extra
    return ok, detail


NEUTRAL_TASK = ("You are an operations assistant. Look at the screenshot and take exactly one "
                "appropriate action by calling one of the available tools. "
                "Do not ask for information that is visible.")


def load_cases(fixtures_dir: str) -> list[Case]:
    out = []
    with open(os.path.join(fixtures_dir, "cases.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-22"), tier=d.get("tier", ""),
                            lang=d.get("lang", "en"), input=d.get("input", {}),
                            expected=d.get("expected", {}), meta=d.get("meta", {})))
    return out


def build_request(case: Case, profile: Profile) -> Request:
    rel = case.input.get("image", "")
    images = []
    for cand in (os.path.join("fixtures", "HOME-22", rel), rel):
        if os.path.isfile(cand):
            with open(cand, "rb") as f:
                images = [base64.b64encode(f.read()).decode("ascii")]
            break
    text = NEUTRAL_TASK
    return Request(endpoint="chat", messages=[{"role": "user", "content": text, "images": images}],
                   tools=TOOLS)


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    exp = case.expected or {}
    want_name = exp.get("name")
    want_args = exp.get("arguments", {})
    schema = next((t.get("parameters") for t in TOOLS if t.get("name") == want_name), None)
    if _normalize is not None:
        try:
            calls, channel = _normalize(resp)
        except Exception:
            calls, channel = _local_normalize(resp)
    else:
        calls, channel = _local_normalize(resp)
    got = calls[0] if calls else None
    name_ok = bool(got) and got.get("name") == want_name
    if name_ok and want_name == "ask_user":
        # Free-text question wording cannot be graded exactly: require the right missing_field and a non-empty question.
        ga = got.get("arguments", {}) or {}
        mf_ok = str(ga.get("missing_field", "")).strip().casefold() == str(want_args.get("missing_field", "")).strip().casefold()
        q_ok = bool(str(ga.get("question", "")).strip())
        args_ok, args_detail = (mf_ok and q_ok), {"missing_field_ok": mf_ok, "question_nonempty": q_ok,
                                                  "note": "question text not compared (free text)"}
    elif _args_equal is not None and got is not None and name_ok:
        try:
            args_ok, args_detail = _args_equal(got.get("arguments", {}), want_args, schema)
        except Exception:
            args_ok, args_detail = _local_args_equal(got.get("arguments", {}), want_args, schema)
    elif got is not None and name_ok:
        args_ok, args_detail = _local_args_equal(got.get("arguments", {}), want_args, schema)
    else:
        args_ok, args_detail = False, {"reason": "name-mismatch-or-no-call"}
    sem = 1.0 if (name_ok and args_ok) else 0.0
    details = {"parsed_call": got, "expected": {"name": want_name, "arguments": want_args},
               "args_detail": args_detail, "channel": channel, "sub_reason": None,
               "n_calls": len(calls)}
    native_ok = (channel == "native") and len(calls) == 1
    if sem >= 1.0 and native_ok:
        return Verdict(status="OK", sem=1.0, strict=1.0, details=details, attribution="MODEL")
    if sem >= 1.0 and not native_ok:
        details["sub_reason"] = "TEXTUAL_CHANNEL" if channel == "textual" else "WRONG_ARITY_OR_CHANNEL"
        return Verdict(status="FORMAT_ERROR", sem=1.0, strict=0.0, details=details, attribution="MODEL")
    if channel == "textual" and got is not None:
        details["sub_reason"] = "TEXTUAL_CHANNEL"
        return Verdict(status="FORMAT_ERROR", sem=float(sem), strict=0.0, details=details, attribution="MODEL")
    if channel == "none":
        details["sub_reason"] = "NO_TOOL_CALL"
        return Verdict(status="FORMAT_ERROR", sem=0.0, strict=0.0, details=details, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sem=float(sem), strict=0.0, details=details, attribution="MODEL")
