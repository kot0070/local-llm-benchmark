"""HOME-01 multilingual intent test (owner: TASK_B2)."""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-01", version="n1", title="Multilingual customer message understanding",
            family="MULTILING", home="aya-expanse:8b", kind="chat", mode="R0",
            requires=["text"], num_predict=256, think_extra=2048,
            num_ctx=4096, timeout_s=120, core_n=12, empty_ok=False)

INTENTS = ["order_status", "refund", "complaint", "delivery_change", "account_access",
           "technical_issue", "billing_error", "cancellation"]
URGENCIES = ["low", "medium", "high", "critical"]
SPEC = {"intent": "exact", "urgency": "exact", "entity_ids": "set",
        "amount": "num", "date": "date", "language": "exact"}

SYSTEM = ("You classify customer support messages. Return ONLY a JSON object with keys: "
          '"intent" (one of order_status, refund, complaint, delivery_change, account_access, '
          'technical_issue, billing_error, cancellation), "urgency" (low, medium, high, critical), '
          '"entity_ids" (array of verbatim IDs such as ORD-48213), "amount" (number or null), '
          '"date" (ISO YYYY-MM-DD or null), "language" (ISO 639-1 code). No prose, no code fences. '
          "Intents: order_status = customer asks where their order or parcel is; "
          "refund = customer asks for money back for a charge; "
          "complaint = customer complains about a wrong charge or poor service; "
          "delivery_change = customer asks to change the delivery address or date; "
          "account_access = customer cannot log in or needs access restored; "
          "technical_issue = device or service error, something is not working; "
          "billing_error = invoice is wrong or double-charged and needs correction; "
          "cancellation = customer wants to cancel the subscription or close the account. "
          "Urgency rubric (label strictly by this rubric using explicit cues in the text): "
          "critical = service/production down NOW or safety/fraud/unauthorized-access risk NOW; "
          "high = money already lost or wrongly charged, or deadline within 24 hours / by tomorrow; "
          "medium = problem affecting use but a workaround exists, or deadline in a few days / beyond 24 hours; "
          "low = general question or information request only, no problem.")


def _fallback_extract(text):
    s = text.strip()
    fenced = "```" in text
    try:
        obj = json.loads(s)
        return obj, {"strict": True, "lenient": True, "fenced": fenced, "prose": False}
    except Exception:
        pass
    cleaned = re.sub(r"```\w*\n?", " ", text)
    cleaned = cleaned.replace("```", " ")
    dec = json.JSONDecoder()
    for m in re.finditer(r"[\{\[]", cleaned):
        try:
            obj, _ = dec.raw_decode(cleaned[m.start():])
            return obj, {"strict": False, "lenient": True, "fenced": fenced, "prose": True}
        except Exception:
            continue
    return None, {"strict": False, "lenient": False, "fenced": fenced, "prose": True}


def _fallback_compare(got, expected, spec):
    def num_eq(a, b):
        if a is None and b is None:
            return 1.0
        if a is None or b is None:
            return 0.0
        try:
            return 1.0 if abs(float(a) - float(b)) < 1e-9 else 0.0
        except Exception:
            return 0.0
    def date_eq(a, b):
        if a is None and b is None:
            return 1.0
        if a is None or b is None:
            return 0.0
        na = str(a).strip().replace("/", "-")[:10]
        nb = str(b).strip().replace("/", "-")[:10]
        return 1.0 if na == nb else 0.0
    def set_f1(a, b):
        a = a if isinstance(a, list) else ([a] if a is not None else [])
        b = b if isinstance(b, list) else ([b] if b is not None else [])
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        ca, cb = Counter(str(x) for x in a), Counter(str(x) for x in b)
        inter = sum((ca & cb).values())
        if inter == 0:
            return 0.0
        return 2 * inter / (sum(ca.values()) + sum(cb.values()))
    per = {}
    for field, typ in spec.items():
        if not isinstance(got, dict) or field not in got:
            per[field] = 0.0
            continue
        g, e = got[field], expected.get(field)
        if typ == "exact":
            per[field] = 1.0 if g == e else 0.0
        elif typ == "ci":
            per[field] = 1.0 if str(g).casefold() == str(e).casefold() else 0.0
        elif typ == "num":
            per[field] = num_eq(g, e)
        elif typ.startswith("num_tol:"):
            try:
                tol = float(typ.split(":", 1)[1])
                if g is None and e is None:
                    per[field] = 1.0
                elif g is None or e is None:
                    per[field] = 0.0
                else:
                    per[field] = 1.0 if abs(float(g) - float(e)) <= tol else 0.0
            except Exception:
                per[field] = 0.0
        elif typ == "date":
            per[field] = date_eq(g, e)
        elif typ == "set":
            per[field] = set_f1(g, e)
        elif typ == "set_ci":
            gg = [str(x).casefold() for x in (g if isinstance(g, list) else [g])]
            ee = [str(x).casefold() for x in (e if isinstance(e, list) else [e])]
            per[field] = set_f1(gg, ee)
        elif typ == "null":
            per[field] = 1.0 if (g is None) == (e is None) else 0.0
        else:
            per[field] = 1.0 if g == e else 0.0
    mean = sum(per.values()) / len(per) if per else 0.0
    return mean, per


try:
    from bench.validate.jsonx import compare_fields as _cf, extract_json as _ej
    _HAS_JSONX = True
except ImportError:
    _ej, _cf = _fallback_extract, _fallback_compare
    _HAS_JSONX = False


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
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-01"),
                              tier=d.get("tier", ""), lang=d.get("lang", "en"),
                              input=d.get("input", {}), expected=d.get("expected"),
                              meta=d.get("meta", {})))
    return cases


def build_request(case: Case, profile: Profile) -> Request:
    msg = case.input.get("message", "")
    return Request(endpoint="chat",
                   messages=[{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": msg}],
                   options={})


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    text = resp.content or ""
    langs = profile.langs if profile.langs is not None else ["multi"]
    obj, info = _ej(text)
    contract_ok = bool(info.get("strict")) and isinstance(obj, dict)
    if obj is None or not isinstance(obj, dict):
        return Verdict(status="FORMAT_ERROR", sub_reason="unparseable", sem=0.0, strict=0.0,
                       details={"parsed": None, "expected": case.expected,
                                "info": info, "channel": "none"}, attribution="MODEL")
    sem, per = _cf(obj, case.expected, SPEC)
    # jsonx "num" cannot score None == None (float(None) raises); a null amount
    # matching a null expectation is correct, so credit it here.
    if case.expected.get("amount") is None and obj.get("amount") is None:
        n = max(1, len(SPEC))
        old = per.get("amount", 0.0)
        old_s = old.get("score", 0.0) if isinstance(old, dict) else float(old or 0.0)
        sem = (sem * n - old_s + 1.0) / n
        if isinstance(per.get("amount"), dict):
            per["amount"]["score"] = 1.0
        else:
            per["amount"] = 1.0
    sem = float(max(0.0, min(1.0, sem)))
    doc = ("multi" in (langs or [])) or (case.lang in (langs or []))
    details = {"parsed": obj, "expected": case.expected, "per_field": per,
               "info": info, "channel": "none", "lang_documented": doc}
    if not contract_ok:
        reason = "code_fence" if info.get("fenced") else "prose_around_json"
        return Verdict(status="FORMAT_ERROR", sub_reason=reason, sem=sem, strict=0.0,
                       details=details, attribution="MODEL")
    if sem >= 1.0 - 1e-9:
        return Verdict(status="OK", sub_reason="exact_match", sem=sem, strict=sem,
                       details=details, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sub_reason="field_mismatch", sem=sem, strict=sem,
                   details=details, attribution="MODEL")
