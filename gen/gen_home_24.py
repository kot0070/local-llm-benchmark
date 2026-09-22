"""Generator for HOME-24 single-turn function calling (owner: TASK_C)."""
from __future__ import annotations

import hashlib
import json
import os
import random

TEST_ID = "HOME-24"
SEED = 2407

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


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_cases() -> list[dict]:
    rng = random.Random(SEED)
    raw: list[dict] = []
    # Straightforward calls (14).
    straight = [
        ("What is the weather in Paris in celsius?", "get_weather", {"city": "Paris", "unit": "celsius"}, "easy"),
        ("Weather in Kyiv in fahrenheit please.", "get_weather", {"city": "Kyiv", "unit": "fahrenheit"}, "easy"),
        ("Convert 100 USD to EUR.", "convert_currency", {"amount": 100, "from_currency": "USD", "to_currency": "EUR"}, "easy"),
        ("Convert 250.5 GBP to USD.", "convert_currency", {"amount": 250.5, "from_currency": "GBP", "to_currency": "USD"}, "medium"),
        ("Create an urgent ticket for C001 about broken lamp.", "create_ticket", {"customer_id": "C001", "subject": "broken lamp", "priority": "urgent"}, "easy"),
        ("Open a low priority ticket for C003: question about delivery.", "create_ticket", {"customer_id": "C003", "subject": "question about delivery", "priority": "low"}, "easy"),
        ("Schedule 'Sprint review' on 2026-10-05 for 60 minutes.", "schedule_meeting", {"title": "Sprint review", "date": "2026-10-05", "duration_min": 60}, "easy"),
        ("Translate 'Good morning' to French.", "translate_text", {"text": "Good morning", "target_lang": "fr"}, "easy"),
        ("Translate 'Thank you very much' to Ukrainian.", "translate_text", {"text": "Thank you very much", "target_lang": "uk"}, "medium"),
        ("Book a flight from Kyiv to Warsaw on 2026-11-02 for 2 seats.", "book_flight", {"origin": "Kyiv", "destination": "Warsaw", "date": "2026-11-02", "seats": 2}, "medium"),
        ("What is the price of 80 with 15 percent off?", "calculate_discount", {"price": 80, "percent": 15}, "easy"),
        ("Calculate discount: price 199.99 percent 10.", "calculate_discount", {"price": 199.99, "percent": 10}, "medium"),
        ("Remind bob@example.com to pay invoice on 2026-09-30: 'Please pay invoice INV-42'.", "send_reminder", {"to": "bob@example.com", "message": "Please pay invoice INV-42", "send_at": "2026-09-30"}, "medium"),
        ("Schedule 'Dentist' on 2026-12-01 for 30 minutes.", "schedule_meeting", {"title": "Dentist", "date": "2026-12-01", "duration_min": 30}, "easy"),
    ]
    for req, name, args, tier in straight:
        raw.append({"req": req, "call": {"name": name, "arguments": args}, "tier": tier, "kind": "direct"})
    # Choice between similar functions (5 = ~16%).
    similar = [
        ("Send a reminder email to carla@example.com 'Renew contract' on 2026-10-01 (not a support ticket).", "send_reminder", {"to": "carla@example.com", "message": "Renew contract", "send_at": "2026-10-01"}, "medium"),
        ("File a support ticket for C002 'Late package' priority high (not a reminder).", "create_ticket", {"customer_id": "C002", "subject": "Late package", "priority": "high"}, "medium"),
        ("What is 200 EUR in USD? Use currency conversion, not discount.", "convert_currency", {"amount": 200, "from_currency": "EUR", "to_currency": "USD"}, "hard"),
        ("Apply 20 percent discount to price 150 (discount, not currency conversion).", "calculate_discount", {"price": 150, "percent": 20}, "hard"),
        ("Book flight Berlin to Paris on 2026-10-20, 1 seat (travel booking, not a meeting).", "book_flight", {"origin": "Berlin", "destination": "Paris", "date": "2026-10-20", "seats": 1}, "hard"),
    ]
    for req, name, args, tier in similar:
        raw.append({"req": req, "call": {"name": name, "arguments": args}, "tier": tier, "kind": "similar"})
    # Missing required argument -> no call (3 = 10%).
    missing = [
        "Book a flight to Paris (no other details given).",
        "Schedule a meeting tomorrow (no title, date or duration specified).",
        "Convert some money to EUR (no amount or source currency).",
    ]
    for req in missing:
        raw.append({"req": req, "call": None, "tier": "hard", "kind": "missing"})
    # No-call general knowledge / chit-chat (8 = ~27%).
    nocall = [
        "What is the capital of France?",
        "Explain in one sentence why the sky is blue.",
        "Who wrote 'Pride and Prejudice'?",
        "What is 12 times 8?",
        "Summarise the plot of a fictional story about a lighthouse keeper.",
        "Is water wet? Answer briefly.",
        "Name three primary colours.",
        "What year comes after 2026?",
    ]
    for req in nocall:
        raw.append({"req": req, "call": None, "tier": "easy" if len(raw) % 2 == 0 else "medium", "kind": "nocall"})
    assert len(raw) == 30, len(raw)
    # Verify ground truth: schema compliance.
    schemas = {t["function"]["name"]: t["function"]["parameters"] for t in TOOLS_24}
    for r in raw:
        c = r["call"]
        if c is None:
            continue
        sch = schemas.get(c["name"])
        assert sch is not None, c["name"]
        for req_key in sch.get("required", []):
            assert req_key in c["arguments"], f"{c['name']} missing {req_key}"
        # Enum check.
        for k, v in c["arguments"].items():
            prop = sch["properties"].get(k, {})
            if "enum" in prop:
                assert v in prop["enum"], f"{c['name']}.{k}={v} not in enum"
    # Oracle recompute via toolsx.args_equal: expected call equals itself.
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from bench.validate.toolsx import args_equal
    for r in raw:
        c = r["call"]
        if c is None:
            continue
        eq, _ = args_equal(dict(c["arguments"]), dict(c["arguments"]), schemas[c["name"]])
        assert eq, f"self-equality failed for {c}"
        neq, _ = args_equal(dict(c["arguments"]), {"__bogus__": 1}, schemas[c["name"]])
        assert not neq
    # Stratified interleave by tier: easy, medium, hard repeating.
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for r in raw:
        by_tier[r["tier"]].append(r)
    for v in by_tier.values():
        v.sort(key=lambda x: x["req"])
    order = []
    idx = {"easy": 0, "medium": 0, "hard": 0}
    cycle = ["easy", "medium", "hard"]
    ci = 0
    total = len(raw)
    while len(order) < total:
        placed = False
        for _ in range(3):
            t = cycle[ci % 3]
            ci += 1
            if idx[t] < len(by_tier[t]):
                order.append((t, by_tier[t][idx[t]]))
                idx[t] += 1
                placed = True
                break
        if not placed:
            break
    cases = []
    for i, (tier, r) in enumerate(order):
        cid = f"HOME-24-{i+1:02d}"
        cases.append({"id": cid, "test_id": TEST_ID, "tier": tier, "lang": "en",
                      "input": {"user_request": r["req"]},
                      "expected": {"expected_call": r["call"]},
                      "meta": {"kind": r["kind"]}})
    # Final check: distribution.
    assert sum(1 for c in cases if c["expected"]["expected_call"] is None) >= 10
    return cases


def main() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outdir = os.path.join(root, "fixtures", "HOME-24")
    os.makedirs(outdir, exist_ok=True)
    cases = _build_cases()
    cpath = os.path.join(outdir, "cases.jsonl")
    with open(cpath, "w", encoding="utf-8", newline="\n") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    files = {}
    for fn in sorted(os.listdir(outdir)):
        if fn == "manifest.json":
            continue
        files[fn] = _sha256_file(os.path.join(outdir, fn))
    manifest = {"test_id": TEST_ID, "seed": SEED, "n_cases": len(cases), "files": files}
    mpath = os.path.join(outdir, "manifest.json")
    with open(mpath, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return outdir


if __name__ == "__main__":
    print(main())
