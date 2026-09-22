"""HOME-21 long tool chains (owner: TASK_C)."""
from __future__ import annotations

import copy
import json
import os

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-21", version="n1", title="Long tool chains", family="TOOLS",
            home="lfm2.5:8b", kind="tools_loop", mode="R0", requires=["text", "tools"],
            num_predict=512, think_extra=1024, num_ctx=8192, timeout_s=900,
            core_n=5, empty_ok=False, max_turns=8)


def load_cases(fixtures_dir: str) -> list[Case]:
    path = os.path.join(fixtures_dir, "cases.jsonl")
    cases: list[Case] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-21"), tier=d.get("tier", ""),
                              lang=d.get("lang", "en"), input=d.get("input", {}),
                              expected=d.get("expected", {}), meta=d.get("meta", {})))
    return cases


def _norm(s) -> str:
    try:
        from bench.validate.textmetrics import norm_text
        return norm_text(s)
    except Exception:
        import unicodedata
        return " ".join(unicodedata.normalize("NFKC", str(s)).casefold().split())


def _deep_equal(got, exp) -> bool:
    if isinstance(exp, dict) and isinstance(got, dict):
        for k, v in exp.items():
            if k not in got or not _deep_equal(got[k], v):
                return False
        return True
    if isinstance(exp, list) and isinstance(got, list):
        if len(got) != len(exp):
            return False
        return all(_deep_equal(a, b) for a, b in zip(got, exp))
    if isinstance(exp, bool) or isinstance(got, bool):
        return got is exp
    if isinstance(exp, (int, float)) and isinstance(got, (int, float)):
        try:
            return abs(float(got) - float(exp)) <= 0.005  # money values: half a cent
        except Exception:
            return False
    if isinstance(exp, str) and isinstance(got, str):
        return _norm(got) == _norm(exp)
    return got == exp


def _check_state(env, expected: dict) -> tuple[bool, dict]:
    snap = env.snapshot()
    det: dict = {"snapshot": snap}
    ok = True
    exp_orders = (expected or {}).get("expected_orders")
    if isinstance(exp_orders, dict):
        good = all(snap["orders"].get(k) == v for k, v in exp_orders.items())
        det["orders_ok"] = good
        if not good:
            ok = False
    if (expected or {}).get("orders_exact"):
        oe = (expected or {}).get("orders_exact")
        det["orders_exact_ok"] = (snap["orders"] == oe)
        if snap["orders"] != oe:
            ok = False
    exp_t = (expected or {}).get("expected_tickets", None)
    if isinstance(exp_t, int):
        det["tickets_ok"] = (len(snap["tickets"]) == exp_t)
        if len(snap["tickets"]) != exp_t:
            ok = False
    tmatch = (expected or {}).get("ticket_match")
    if isinstance(tmatch, dict) and tmatch:
        found = any(all(t.get(k) == v for k, v in tmatch.items() if k != "subject_contains") and
                    (tmatch.get("subject_contains", "").casefold() in str(t.get("subject", "")).casefold()
                     if tmatch.get("subject_contains") else True)
                    for t in snap["tickets"])
        det["ticket_match_ok"] = found
        if not found:
            ok = False
    exp_e = (expected or {}).get("expected_emails", None)
    if isinstance(exp_e, int):
        det["emails_ok"] = (len(snap["sent_emails"]) == exp_e)
        if len(snap["sent_emails"]) != exp_e:
            ok = False
    ematch = (expected or {}).get("email_match")
    if isinstance(ematch, dict) and ematch:
        found = any(all(str(e.get(k, "")).strip().casefold() == str(v).strip().casefold()
                        for k, v in ematch.items() if k not in ("subject_contains", "body_contains")) and
                    (ematch.get("subject_contains", "").casefold() in str(e.get("subject", "")).casefold()
                     if ematch.get("subject_contains") else True)
                    for e in snap["sent_emails"])
        det["email_match_ok"] = found
        if not found:
            ok = False
    return ok, det



def _shape(v):
    """Placeholder skeleton of the expected result: key names are part of the contract, values are not."""
    if isinstance(v, dict):
        return {k: _shape(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_shape(v[0])] if v else []
    if isinstance(v, bool):
        return "<true|false>"
    if isinstance(v, (int, float)):
        return "<number>"
    if isinstance(v, str):
        return "<string>"
    return None


def final_contract(expected: dict) -> str:
    """Smoke audit: exact-mode results use fixed key names, so the model must be told the shape."""
    exp = expected or {}
    res = exp.get("result")
    if exp.get("result_mode", "exact") == "exact" and res is not None:
        shape = json.dumps({"result": _shape(res)}, ensure_ascii=False)
        return ("Final answer contract: output ONLY JSON of exactly this shape " + shape
                + " (replace each placeholder with the value; numbers as JSON numbers) with no extra text.")
    return 'Final answer contract: output ONLY JSON {"result": ...} with no extra text.'


def run_case(case: Case, profile: Profile, chat_fn) -> tuple[Verdict, list[dict]]:
    from bench.tests._mockenv import MockEnv
    from bench.validate.jsonx import extract_json
    from bench.validate.toolsx import normalize_calls
    env = MockEnv()
    tools = MockEnv.get_tools()
    initial_orders = dict(env.snapshot()["orders"])
    user_request = case.input.get("user_request", "")
    expected = case.expected or {}
    max_turns = int(META.get("max_turns", 8))
    minimal = int(expected.get("minimal_steps", 0) or 0)
    messages: list[dict] = []
    if getattr(profile, "system", None):
        messages.append({"role": "system", "content": profile.system})
    messages.append({"role": "user", "content": user_request + "\n\n" + final_contract(expected)})
    transcript: list[dict] = [{"role": "user", "content": messages[-1]["content"]}]
    textual_used = False
    channels: list[str] = []
    final_resp: Response | None = None
    steps = 0
    for _ in range(max_turns):
        req = Request(endpoint="chat", messages=list(messages), tools=copy.deepcopy(tools))
        try:
            resp = chat_fn(req)
        except Exception as e:
            return Verdict(status="HARNESS_ERROR", sub_reason="CHAT_FN", sem=0.0, strict=0.0,
                           details={"error": str(e)}, attribution="HARNESS"), transcript
        final_resp = resp
        native = list(getattr(resp, "tool_calls", None) or [])
        if native:
            calls, ch = normalize_calls(resp)
            channels.append(ch)
            steps += 1
            messages.append({"role": "assistant", "content": resp.content or "", "tool_calls": resp.tool_calls})
            transcript.append({"role": "assistant", "content": resp.content or "", "tool_calls": resp.tool_calls, "channel": ch})
            if not calls:
                continue
            for c in calls:
                res = env.call(c["name"], c["arguments"] if isinstance(c["arguments"], dict) else {})
                messages.append({"role": "tool", "content": json.dumps(res, ensure_ascii=False), "tool_name": c["name"]})
                transcript.append({"role": "tool", "content": json.dumps(res, ensure_ascii=False), "tool_name": c["name"]})
            continue
        calls_t, _ = normalize_calls(resp)
        if calls_t:
            textual_used = True
            channels.append("textual")
            steps += 1
            messages.append({"role": "assistant", "content": resp.content or ""})
            transcript.append({"role": "assistant", "content": resp.content or "", "channel": "textual"})
            for c in calls_t:
                res = env.call(c["name"], c["arguments"] if isinstance(c["arguments"], dict) else {})
                messages.append({"role": "tool", "content": json.dumps(res, ensure_ascii=False), "tool_name": c["name"]})
                transcript.append({"role": "tool", "content": json.dumps(res, ensure_ascii=False), "tool_name": c["name"]})
            continue
        messages.append({"role": "assistant", "content": resp.content or ""})
        transcript.append({"role": "assistant", "content": resp.content or ""})
        break
    content = (final_resp.content or "") if final_resp is not None else ""
    obj, info = extract_json(content)
    broken = bool(info.get("fenced") or info.get("prose")) or textual_used
    parsed = obj if isinstance(obj, dict) else None
    if parsed is not None and set(parsed.keys()) != {"result"}:
        broken = True
    got_result = parsed.get("result") if parsed is not None else None
    answer_ok = False
    if parsed is not None:
        exp_result = expected.get("result", "__MISSING__")
        mode = expected.get("result_mode", "exact")
        must_contain = expected.get("must_contain", []) or []
        if mode == "contains":
            s = got_result if isinstance(got_result, str) else json.dumps(got_result, ensure_ascii=False)
            answer_ok = all(str(m).casefold() in s.casefold() for m in must_contain) if must_contain else True
        else:
            if exp_result == "__MISSING__":
                answer_ok = True
            elif isinstance(exp_result, str) and isinstance(got_result, str):
                answer_ok = (_norm(got_result) == _norm(exp_result))
            else:
                answer_ok = _deep_equal(got_result, exp_result)
            if must_contain:
                s = got_result if isinstance(got_result, str) else json.dumps(got_result, ensure_ascii=False)
                answer_ok = answer_ok and all(str(m).casefold() in s.casefold() for m in must_contain)
    state_ok, state_det = _check_state(env, expected)
    mut_calls = [c for c in env.calls if c["name"] in ("cancel_order", "send_email")]
    unnecessary = 0
    if expected.get("forbid_mutations"):
        unnecessary += len(mut_calls)
    else:
        exp_orders = expected.get("expected_orders", {}) or {}
        changed = [o for o, st in env.snapshot()["orders"].items() if initial_orders.get(o) != st]
        for o in changed:
            if o not in exp_orders:
                unnecessary += 1
    n_calls = len(env.calls)
    if parsed is None:
        sem = 0.5 if state_ok else 0.0
        details = {"calls": env.calls, "channel": channels[-1] if channels else "none",
                   "channels": channels, "textual": textual_used, "state_ok": state_ok,
                   "answer_ok": False, "state": state_det, "unnecessary_mutations": unnecessary,
                   "steps": n_calls, "minimal_steps": minimal,
                   "fenced": bool(info.get("fenced")), "prose": bool(info.get("prose"))}
        return Verdict(status="FORMAT_ERROR", sub_reason="NO_JSON", sem=sem, strict=0.0,
                       details=details, attribution="MODEL"), transcript
    if state_ok and answer_ok:
        sem = 1.0
    elif state_ok:
        sem = 0.5
    else:
        sem = 0.0
    details = {"calls": env.calls, "channel": channels[-1] if channels else "none",
               "channels": channels, "textual": textual_used, "state_ok": state_ok,
               "answer_ok": answer_ok, "state": state_det, "unnecessary_mutations": unnecessary,
               "got_result": got_result, "expected_result": expected.get("result"),
               "steps": n_calls, "minimal_steps": minimal,
               "fenced": bool(info.get("fenced")), "prose": bool(info.get("prose")),
               "strict_json": bool(info.get("strict"))}
    if broken or textual_used:
        return Verdict(status="FORMAT_ERROR", sub_reason="TEXTUAL_CALL" if textual_used else "CONTRACT_BROKEN",
                       sem=sem, strict=0.0, details=details, attribution="MODEL"), transcript
    if sem >= 1.0:
        return Verdict(status="OK", sub_reason=None, sem=1.0, strict=1.0,
                       details=details, attribution="MODEL"), transcript
    return Verdict(status="WRONG_ANSWER", sub_reason="BAD_STATE" if not state_ok else "BAD_ANSWER",
                   sem=sem, strict=0.0, details=details, attribution="MODEL"), transcript
