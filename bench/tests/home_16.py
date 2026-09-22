"""HOME-16 routing test (owner: TASK_B2)."""
from __future__ import annotations

import json
import re

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-16", version="n1", title="Support request routing with policy",
            family="ROUTE", home="qwen3:1.7b", kind="chat", mode="R0",
            requires=["text"], num_predict=64, think_extra=1024,
            num_ctx=4096, timeout_s=90, core_n=20, empty_ok=False)

SYSTEM = ("You route customer requests. Read the routing policy in the user message, then return ONLY a JSON object "
          'with keys: "route" (one of ACCOUNT, BILLING, DELIVERY, TECH, SALES, RETENTION, SAFETY, LEGAL, HR, '
          'IT_ACCESS, ESCALATE), "reason_code" (the policy rule that fired). No prose, no code fences.')


def _fallback_extract(text):
    s = text.strip()
    fenced = "```" in text
    try:
        return json.loads(s), {"strict": True, "lenient": True, "fenced": fenced, "prose": False}
    except Exception:
        pass
    cleaned = re.sub(r"```\w*\n?", " ", text).replace("```", " ")
    dec = json.JSONDecoder()
    for m in re.finditer(r"[\{\[]", cleaned):
        try:
            obj, _ = dec.raw_decode(cleaned[m.start():])
            return obj, {"strict": False, "lenient": True, "fenced": fenced, "prose": True}
        except Exception:
            continue
    return None, {"strict": False, "lenient": False, "fenced": fenced, "prose": True}


try:
    from bench.validate.jsonx import extract_json as _ej
except ImportError:
    _ej = _fallback_extract


def load_cases(fixtures_dir: str) -> list[Case]:
    import os
    path = os.path.join(fixtures_dir, "cases.jsonl")
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-16"),
                              tier=d.get("tier", ""), lang=d.get("lang", "en"),
                              input=d.get("input", {}), expected=d.get("expected"),
                              meta=d.get("meta", {})))
    return cases


def build_request(case: Case, profile: Profile) -> Request:
    user = ("Routing policy:\n" + case.input.get("policy", "") +
            "\n\nCustomer request:\n" + case.input.get("message", ""))
    return Request(endpoint="chat",
                   messages=[{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": user}],
                   options={})


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    text = resp.content or ""
    exp = case.expected or {}
    obj, info = _ej(text)
    contract_ok = bool(info.get("strict")) and isinstance(obj, dict)
    if obj is None or not isinstance(obj, dict):
        return Verdict(status="FORMAT_ERROR", sub_reason="unparseable", sem=0.0, strict=0.0,
                       details={"parsed": None, "expected": exp, "info": info,
                                "reason_code_match": 0.0, "channel": "none"}, attribution="MODEL")
    route = str(obj.get("route", "")).strip().upper()
    reason = str(obj.get("reason_code", "")).strip()
    sem = 1.0 if route == exp.get("route") else 0.0
    rc = 1.0 if reason == exp.get("reason_code") else 0.0
    details = {"parsed": {"route": route, "reason_code": reason}, "expected": exp,
               "info": info, "reason_code_match": rc, "channel": "none"}
    if not contract_ok:
        why = "code_fence" if info.get("fenced") else "prose_around_json"
        return Verdict(status="FORMAT_ERROR", sub_reason=why, sem=sem, strict=0.0,
                       details=details, attribution="MODEL")
    if sem >= 1.0:
        return Verdict(status="OK", sub_reason="route_match", sem=sem, strict=sem,
                       details=details, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sub_reason="route_mismatch", sem=sem, strict=sem,
                   details=details, attribution="MODEL")
