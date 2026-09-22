"""HOME-24 single-turn function calling (owner: TASK_C)."""
from __future__ import annotations

import json
import os

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-24", version="n1", title="Single-turn function calling", family="TOOLS",
            home="functiongemma:270m", kind="chat", mode="R0", requires=["text", "tools"],
            num_predict=128, think_extra=1024, num_ctx=4096, timeout_s=60,
            core_n=15, empty_ok=False)

TOOLS_24 = [
    {"type": "function", "function": {"name": "get_weather", "description": "Get weather for a city.",
     "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}}, "required": ["city", "unit"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "convert_currency", "description": "Convert currency.",
     "parameters": {"type": "object", "properties": {"amount": {"type": "number"}, "from_currency": {"type": "string", "enum": ["USD", "EUR", "GBP", "UAH", "JPY"]}, "to_currency": {"type": "string", "enum": ["USD", "EUR", "GBP", "UAH", "JPY"]}}, "required": ["amount", "from_currency", "to_currency"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "create_ticket", "description": "Create a support ticket.",
     "parameters": {"type": "object", "properties": {"customer_id": {"type": "string"}, "subject": {"type": "string"}, "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}}, "required": ["customer_id", "subject", "priority"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "schedule_meeting", "description": "Schedule a meeting on a date.",
     "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "date": {"type": "string", "description": "YYYY-MM-DD"}, "duration_min": {"type": "integer"}}, "required": ["title", "date", "duration_min"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "send_reminder", "description": "Send a reminder email.",
     "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "message": {"type": "string"}, "send_at": {"type": "string", "description": "YYYY-MM-DD"}}, "required": ["to", "message", "send_at"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "calculate_discount", "description": "Calculate discounted price.",
     "parameters": {"type": "object", "properties": {"price": {"type": "number"}, "percent": {"type": "number"}}, "required": ["price", "percent"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "translate_text", "description": "Translate text.",
     "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "target_lang": {"type": "string", "enum": ["en", "fr", "de", "es", "uk"]}}, "required": ["text", "target_lang"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "book_flight", "description": "Book a flight on a date.",
     "parameters": {"type": "object", "properties": {"origin": {"type": "string"}, "destination": {"type": "string"}, "date": {"type": "string", "description": "YYYY-MM-DD"}, "seats": {"type": "integer"}}, "required": ["origin", "destination", "date", "seats"], "additionalProperties": False}}},
]

SCHEMAS_24 = {t["function"]["name"]: t["function"]["parameters"] for t in TOOLS_24}


def load_cases(fixtures_dir: str) -> list[Case]:
    path = os.path.join(fixtures_dir, "cases.jsonl")
    cases: list[Case] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-24"), tier=d.get("tier", ""),
                              lang=d.get("lang", "en"), input=d.get("input", {}),
                              expected=d.get("expected", {}), meta=d.get("meta", {})))
    return cases


def build_request(case: Case, profile: Profile) -> Request:
    user_request = case.input.get("user_request", "")
    content = (f"{user_request}\n\nCall the matching function with exact arguments. "
               "If no function matches or a required argument is missing, make no call and answer in text.")
    msgs = []
    if getattr(profile, "system", None):
        msgs.append({"role": "system", "content": profile.system})
    msgs.append({"role": "user", "content": content})
    return Request(endpoint="chat", messages=msgs, tools=[dict(t) for t in TOOLS_24])


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    from bench.validate.toolsx import normalize_calls, args_equal
    exp = case.expected or {}
    exp_call = exp.get("expected_call")
    calls, channel = normalize_calls(resp)
    if exp_call is None:
        # Correct behaviour: no call.
        if not calls:
            return Verdict(status="OK", sub_reason=None, sem=1.0, strict=1.0,
                           details={"channel": channel, "all_calls": [], "extra_calls": 0,
                                    "whitespace_padded": False}, attribution="MODEL")
        return Verdict(status="WRONG_ANSWER", sub_reason="UNEXPECTED_CALL", sem=0.0, strict=0.0,
                       details={"channel": channel, "all_calls": calls, "extra_calls": len(calls),
                                "whitespace_padded": False}, attribution="MODEL")
    exp_name = exp_call.get("name", "")
    exp_args = exp_call.get("arguments", {})
    schema = SCHEMAS_24.get(exp_name)
    if not calls:
        return Verdict(status="WRONG_ANSWER", sub_reason="NO_CALL", sem=0.0, strict=0.0,
                       details={"channel": channel, "all_calls": [], "extra_calls": 0,
                                "expected": exp_name, "whitespace_padded": False}, attribution="MODEL")
    first = calls[0]
    # Textual channel is a contract violation for native-call models.
    eq, det = args_equal(first.get("arguments", {}), exp_args, schema)
    name_ok = (first.get("name") == exp_name)
    exact = name_ok and eq
    # Contract: exactly one call ideally; extra calls noted.
    extra = max(0, len(calls) - 1)
    details = {"channel": channel, "all_calls": calls, "extra_calls": extra,
               "expected": exp_name, "name_ok": name_ok,
               "whitespace_padded": bool(det.get("whitespace_padded")),
               "args_detail": det}
    if channel == "textual":
        sem = 1.0 if exact else 0.0
        return Verdict(status="FORMAT_ERROR", sub_reason="TEXTUAL_CALL", sem=sem, strict=0.0,
                       details=details, attribution="MODEL")
    if exact:
        if extra > 0:
            return Verdict(status="FORMAT_ERROR", sub_reason="EXTRA_CALLS", sem=1.0, strict=0.0,
                           details=details, attribution="MODEL")
        return Verdict(status="OK", sub_reason=None, sem=1.0, strict=1.0,
                       details=details, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sub_reason="BAD_CALL", sem=0.0, strict=0.0,
                   details=details, attribution="MODEL")
