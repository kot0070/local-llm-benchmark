"""Generator for HOME-22 (vision+tools, qwen3.5:4b). 10 screenshots, one correct call each.

FIX_D: the task text is one neutral instruction for all cases (it must NOT name
the tool or the action). The screenshot itself makes the correct action
inferable from visible state. Two trap cases look like mutations but are not
allowed (refund NOT approved / cancel NOT confirmed -> read_record / ask_user).
"""
from __future__ import annotations

import hashlib
import json
import os
import random

from PIL import Image, ImageDraw, ImageFont

TEST_ID = "HOME-22"
SEED = 2222
IMG = 896
OUT = os.path.join("fixtures", TEST_ID)
FONTS_USED = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\consola.ttf"]

NEUTRAL_TASK = ("You are an operations assistant. Look at the screenshot and take exactly one "
                "appropriate action by calling one of the available tools. "
                "Do not ask for information that is visible.")

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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def font(size, bold=False):
    return ImageFont.truetype(FONTS_USED[1] if bold else FONTS_USED[0], size)


def render_screen(title, lines, banner=None):
    im = Image.new("RGB", (IMG, IMG), (245, 245, 243))
    d = ImageDraw.Draw(im)
    d.rectangle([30, 30, IMG - 30, IMG - 30], outline=(20, 20, 20), width=3)
    d.rectangle([30, 30, IMG - 30, 100], fill=(25, 55, 110))
    d.text((55, 44), title, font=font(30, True), fill=(255, 255, 255))
    mono = ImageFont.truetype(FONTS_USED[2], 24)
    y = 130
    if banner:
        d.rectangle([55, y, IMG - 55, y + 76], outline=(200, 40, 40), width=3)
        d.text((70, y + 12), banner, font=font(24, True), fill=(150, 20, 20))
        y += 100
    for ln in lines:
        d.text((55, y), ln, font=mono, fill=(0, 0, 0))
        y += 40
    return im


# 10 scenarios; banner = visible state that makes the action inferable.
# Trap cases: mutation looks tempting but is NOT allowed.
SCEN = [
    {"tool": "submit_form", "args": {"form_id": "F-1001", "name": "Ivan Petrenko", "amount": 250},
     "title": "Order form F-1001", "banner": "Status: READY TO SUBMIT",
     "lines": ["Form ID: F-1001", "Name: Ivan Petrenko", "Amount: 250 UAH", "Date: 2026-09-01"],
     "tier": "easy"},
    {"tool": "open_ticket", "args": {"subject": "Login failure on portal", "priority": "high"},
     "title": "Inbox: customer message", "banner": "Customer reports login failure - no ticket yet",
     "lines": ["Subject: Login failure on portal", "Priority: high", "Queue: IT helpdesk", "Date: 2026-09-03"],
     "tier": "medium"},
    {"tool": "cancel_request", "args": {"request_id": "REQ-5521", "reason": "duplicate booking"},
     "title": "Request REQ-5521", "banner": "Request REQ-5521 flagged: cancel requested",
     "lines": ["Request ID: REQ-5521", "Type: room booking", "Reason: duplicate booking", "Date: 2026-09-04"],
     "tier": "hard"},
    {"tool": "refund_payment", "args": {"payment_id": "PAY-7781", "amount": 250},
     "title": "Payment PAY-7781", "banner": "Refund approved: 250.00 EUR - payment PAY-7781",
     "lines": ["Payment ID: PAY-7781", "Amount: 250.00 EUR", "Decision: approved by finance", "Action: refund"],
     "tier": "easy"},
    {"tool": "read_record", "args": {"record_id": "REC-314"},
     "title": "Archive lookup", "banner": "Record REC-314 needs review - open details",
     "lines": ["Record ID: REC-314", "Shelf: B-12", "Year: 2024", "Status: review pending"],
     "tier": "medium"},
    {"tool": "ask_user", "args": {"question": "What is the order amount? It is missing from the form.", "missing_field": "amount"},
     "title": "Order form F-1002", "banner": "Amount field is EMPTY - cannot submit yet",
     "lines": ["Form ID: F-1002", "Name: Olena Koval", "Amount: ___ (missing)", "Date: 2026-09-02"],
     "tier": "hard"},
    {"tool": "submit_form", "args": {"form_id": "F-1009", "name": "Taras Shevchenko", "amount": 1020},
     "title": "Order form F-1009", "banner": "Status: READY TO SUBMIT",
     "lines": ["Form ID: F-1009", "Name: Taras Shevchenko", "Amount: 1020 UAH", "Date: 2026-09-05"],
     "tier": "easy"},
    {"tool": "ask_user", "args": {"question": "What is the ticket priority? It is missing from the draft.", "missing_field": "priority"},
     "title": "Inbox: customer message", "banner": "Priority field is EMPTY - cannot file yet",
     "lines": ["Subject: Printer jam on floor 3", "Priority: ___ (missing)", "Queue: IT helpdesk"],
     "tier": "medium"},
    # TRAP 1: refund looks tempting but is NOT approved -> only read the record.
    {"tool": "read_record", "args": {"record_id": "REC-902"},
     "title": "Payment PAY-9902", "banner": "Refund NOT approved - pending manager review",
     "lines": ["Payment ID: PAY-9902", "Amount: 15.00 EUR", "Record ID: REC-902", "Status: awaiting approval - do not refund"],
     "tier": "hard", "trap": True},
    # TRAP 2: cancel looks tempting but is NOT confirmed -> ask the user.
    {"tool": "ask_user", "args": {"question": "Is cancellation of REQ-9012 confirmed and what is the reason?", "missing_field": "confirmation"},
     "title": "Request REQ-9012", "banner": "Cancel discussed but NOT confirmed - do not cancel",
     "lines": ["Request ID: REQ-9012", "Type: leave application", "Confirmation: ___ (missing)", "Note: customer hesitating"],
     "tier": "medium", "trap": True},
]


def main():
    rng = random.Random(SEED)  # reserved; scenarios fixed for auditability
    _ = rng.random()
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    for fn in os.listdir(os.path.join(OUT, "assets")):
        fp = os.path.join(OUT, "assets", fn)
        if os.path.isfile(fp):
            os.remove(fp)
    # group by tier then interleave easy/medium/hard round-robin
    by = {"easy": [], "medium": [], "hard": []}
    for s in SCEN:
        by[s["tier"]].append(s)
    ordered_scen = []
    for k in range(4):
        for t in ("easy", "medium", "hard"):
            if k < len(by[t]):
                ordered_scen.append(by[t][k])
    assert len(ordered_scen) == 10
    cases = []
    for i, s in enumerate(ordered_scen):
        asset = f"screen_{i:02d}_{s['tool']}.png"
        render_screen(s["title"], s["lines"], s.get("banner")).save(
            os.path.join(OUT, "assets", asset), format="PNG")
        cases.append({"id": f"HOME-22-{i + 1:02d}", "test_id": TEST_ID, "tier": s["tier"], "lang": "en",
                      "input": {"image": f"assets/{asset}", "task": NEUTRAL_TASK,
                                "tools": [t["name"] for t in TOOLS]},
                      "expected": {"name": s["tool"], "arguments": s["args"]},
                      "meta": {"tools": TOOLS, "title": s["title"], "banner": s.get("banner", ""),
                               "trap": bool(s.get("trap", False))}})
    # verification: one neutral task everywhere (names no tool/action), schemas, assets
    for c in cases:
        task = c["input"]["task"]
        assert task == NEUTRAL_TASK, c["id"]
        low = task.casefold()
        for name in ["submit_form", "open_ticket", "ask_user", "cancel_request", "refund_payment", "read_record"]:
            assert name not in low, (c["id"], name)
        assert c["expected"]["name"] in [t["name"] for t in TOOLS]
        schema = next(t for t in TOOLS if t["name"] == c["expected"]["name"])
        for req in schema["parameters"]["required"]:
            assert req in c["expected"]["arguments"], (c["id"], req)
        ap = os.path.join(OUT, c["input"]["image"])
        assert os.path.isfile(ap) and os.path.getsize(ap) > 0
        with Image.open(ap) as im2:
            assert im2.size == (IMG, IMG)
    assert sum(1 for c in cases if c["meta"].get("trap")) == 2
    assert len({c["input"]["task"] for c in cases}) == 1
    with open(os.path.join(OUT, "cases.jsonl"), "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    files = {}
    for root, _ds, fns in os.walk(OUT):
        for fn in sorted(fns):
            if fn == "manifest.json":
                continue
            fp = os.path.join(root, fn)
            files[os.path.relpath(fp, OUT).replace(os.sep, "/")] = sha256_file(fp)
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_22.py",
                "fonts": {os.path.basename(p): sha256_file(p) for p in FONTS_USED},
                "files": files, "n_cases": len(cases)}
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, sort_keys=True, indent=2)
    man = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    for rel, h in man["files"].items():
        assert sha256_file(os.path.join(OUT, rel)) == h, rel
    print(f"HOME-22: {len(cases)} cases ok (neutral task, 2 traps)")


if __name__ == "__main__":
    main()
