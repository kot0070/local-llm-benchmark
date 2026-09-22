"""Generator for HOME-18 short tool loops (owner: TASK_C)."""
from __future__ import annotations

import hashlib
import json
import os

TEST_ID = "HOME-18"
SEED = 1807


def _sha256_file(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_raw():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from bench.tests._mockenv import MockEnv
    scenarios = []
    # 1 parallel weather
    env = MockEnv()
    r1 = env.call("get_weather", {"city": "Paris", "unit": "celsius"})
    r2 = env.call("get_weather", {"city": "Kyiv", "unit": "celsius"})
    assert r1["ok"] and r2["ok"]
    scenarios.append({
        "sid": "parallel_weather", "tier": "medium",
        "user_request": "Get the current weather in Paris and in Kyiv, both in celsius. You must call get_weather for each city.",
        "oracle_calls": [("get_weather", {"city": "Paris", "unit": "celsius"}), ("get_weather", {"city": "Kyiv", "unit": "celsius"})],
        "expected": {"result": {"Paris": r1["temp"], "Kyiv": r2["temp"]}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0, "minimal_steps": 2},
    })
    # 2 dependent
    env = MockEnv()
    c = env.call("get_customer", {"email": "bob@example.com"})
    lo = env.call("list_orders", {"customer_id": "C002"})
    o = env.call("get_order", {"order_id": "ORD-1003"})
    assert c["ok"] and lo["ok"] and o["ok"]
    scenarios.append({
        "sid": "dependent_lookup", "tier": "medium",
        "user_request": "The customer with email bob@example.com asks for the total of order ORD-1003. Look up the customer, list their orders, then get the order details.",
        "oracle_calls": [("get_customer", {"email": "bob@example.com"}), ("list_orders", {"customer_id": "C002"}), ("get_order", {"order_id": "ORD-1003"})],
        "expected": {"result": {"order_id": "ORD-1003", "total": o["total"], "currency": "USD"}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0, "minimal_steps": 3},
    })
    # 3 transform
    env = MockEnv()
    env.call("get_customer", {"email": "alice@example.com"})
    oo = env.call("get_order", {"order_id": "ORD-1001"})
    conv = env.call("convert_currency", {"amount": oo["total"], "from": "USD", "to": "EUR"})
    assert oo["ok"] and conv["ok"]
    scenarios.append({
        "sid": "arg_transform", "tier": "hard",
        "user_request": "Customer alice@example.com wants to know how much order ORD-1001 costs in EUR (the order total is in USD). Look up the order, then convert its total from USD to EUR.",
        "oracle_calls": [("get_customer", {"email": "alice@example.com"}), ("get_order", {"order_id": "ORD-1001"}), ("convert_currency", {"amount": oo["total"], "from": "USD", "to": "EUR"})],
        "expected": {"result": {"amount": conv["converted"], "currency": "EUR"}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0, "minimal_steps": 3},
    })
    # 4 no-call
    scenarios.append({
        "sid": "no_call", "tier": "easy",
        "user_request": "What is the capital of France? Answer directly without calling any tools.",
        "oracle_calls": [],
        "expected": {"result": "Paris", "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0,
                     "forbid_mutations": True, "minimal_steps": 0},
    })
    # 5 missing info
    scenarios.append({
        "sid": "missing_info", "tier": "hard",
        "user_request": "Please cancel my order.",
        "oracle_calls": [],
        "expected": {"result_mode": "contains", "must_contain": ["order"], "result": None,
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0,
                     "forbid_mutations": True, "minimal_steps": 0},
    })
    # 6 explicit cancel
    env = MockEnv()
    cc = env.call("cancel_order", {"order_id": "ORD-1005"})
    assert cc["ok"]
    scenarios.append({
        "sid": "cancel_explicit", "tier": "easy",
        "user_request": "Please cancel order ORD-1005. I confirm I want it cancelled.",
        "oracle_calls": [("cancel_order", {"order_id": "ORD-1005"})],
        "expected": {"result": {"order_id": "ORD-1005", "status": "cancelled"}, "result_mode": "exact",
                     "expected_orders": {"ORD-1005": "cancelled"}, "expected_tickets": 0, "expected_emails": 0, "minimal_steps": 1},
    })
    # 7 implicit cancel -> must not mutate
    env = MockEnv()
    st = env.call("get_order", {"order_id": "ORD-1003"})
    assert st["ok"]
    scenarios.append({
        "sid": "cancel_implicit", "tier": "hard",
        "user_request": "I am thinking about cancelling ORD-1003, but I am not sure. What is its current status? Do NOT cancel anything.",
        "oracle_calls": [("get_order", {"order_id": "ORD-1003"})],
        "expected": {"result": {"order_id": "ORD-1003", "status": st["status"]}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0,
                     "forbid_mutations": True, "minimal_steps": 1},
    })
    # 8 ticket
    env = MockEnv()
    tk = env.call("create_ticket", {"customer_id": "C003", "subject": "Late delivery of headphones", "priority": "high"})
    assert tk["ok"]
    scenarios.append({
        "sid": "ticket_flow", "tier": "medium",
        "user_request": "Create a high priority ticket for customer C003 with subject 'Late delivery of headphones'.",
        "oracle_calls": [("create_ticket", {"customer_id": "C003", "subject": "Late delivery of headphones", "priority": "high"})],
        "expected": {"result": {"ticket_id": tk["ticket_id"], "priority": "high"}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 1,
                     "ticket_match": {"customer_id": "C003", "priority": "high", "subject_contains": "Late"},
                     "expected_emails": 0, "minimal_steps": 1},
    })
    # 9 email
    env = MockEnv()
    em = env.call("send_email", {"to": "alice@example.com", "subject": "Your refund", "body": "Your refund of 10 USD was processed."})
    assert em["ok"]
    scenarios.append({
        "sid": "email_flow", "tier": "easy",
        "user_request": "Send an email to alice@example.com with subject 'Your refund' and body 'Your refund of 10 USD was processed.'.",
        "oracle_calls": [("send_email", {"to": "alice@example.com", "subject": "Your refund", "body": "Your refund of 10 USD was processed."})],
        "expected": {"result": {"sent": True, "to": "alice@example.com"}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 1,
                     "email_match": {"to": "alice@example.com", "subject_contains": "refund"}, "minimal_steps": 1},
    })
    # 10 refund
    env = MockEnv()
    rf = env.call("compute_refund", {"order_id": "ORD-1004", "reason": "damaged"})
    assert rf["ok"]
    scenarios.append({
        "sid": "refund_flow", "tier": "medium",
        "user_request": "Compute the refund for order ORD-1004 with reason 'damaged'.",
        "oracle_calls": [("compute_refund", {"order_id": "ORD-1004", "reason": "damaged"})],
        "expected": {"result": {"order_id": "ORD-1004", "refund_amount": rf["refund_amount"]}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0, "minimal_steps": 1},
    })
    assert len(scenarios) == 10
    # Verify each oracle sequence replays cleanly on a fresh env.
    for s in scenarios:
        e2 = MockEnv()
        for name, args in s["oracle_calls"]:
            r = e2.call(name, args)
            assert r.get("ok"), f"oracle failed {s['sid']} {name} {r}"
        # Verify expected state matches oracle snapshot (orders subset + counts).
        snap = e2.snapshot()
        for oid, st in s["expected"].get("expected_orders", {}).items():
            assert snap["orders"].get(oid) == st, f"{s['sid']} order {oid}"
        if isinstance(s["expected"].get("expected_tickets"), int):
            assert len(snap["tickets"]) == s["expected"]["expected_tickets"], s["sid"]
        if isinstance(s["expected"].get("expected_emails"), int):
            assert len(snap["sent_emails"]) == s["expected"]["expected_emails"], s["sid"]
    return scenarios


def main() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outdir = os.path.join(root, "fixtures", "HOME-18")
    os.makedirs(outdir, exist_ok=True)
    scenarios = _build_raw()
    # Stratified interleave easy/medium/hard.
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for s in scenarios:
        by_tier[s["tier"]].append(s)
    for v in by_tier.values():
        v.sort(key=lambda x: x["sid"])
    order = []
    idx = {"easy": 0, "medium": 0, "hard": 0}
    cycle = ["easy", "medium", "hard"]
    ci = 0
    while len(order) < len(scenarios):
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
    for i, (tier, s) in enumerate(order):
        cid = f"HOME-18-{i+1:02d}"
        cases.append({"id": cid, "test_id": TEST_ID, "tier": tier, "lang": "en",
                      "input": {"user_request": s["user_request"], "scenario": s["sid"]},
                      "expected": s["expected"],
                      "meta": {"scenario": s["sid"], "minimal_steps": s["expected"].get("minimal_steps", 0)}})
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
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return outdir


if __name__ == "__main__":
    print(main())
