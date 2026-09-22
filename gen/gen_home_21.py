"""Generator for HOME-21 long tool chains (owner: TASK_C)."""
from __future__ import annotations

import hashlib
import json
import os

TEST_ID = "HOME-21"
SEED = 2107


def _sha256_file(path: str) -> str:
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
    # T1 cancel + refund + notify (5 calls)
    env = MockEnv()
    env.call("get_customer", {"email": "bob@example.com"})
    env.call("get_order", {"order_id": "ORD-1003"})
    env.call("cancel_order", {"order_id": "ORD-1003"})
    rf = env.call("compute_refund", {"order_id": "ORD-1003", "reason": "customer_request"})
    env.call("send_email", {"to": "bob@example.com", "subject": "Cancellation of ORD-1003", "body": "Order ORD-1003 cancelled. Refund 250.0 USD."})
    assert rf["ok"]
    scenarios.append({
        "sid": "cancel_refund_notify", "tier": "hard",
        "user_request": "Customer bob@example.com wants to cancel order ORD-1003, get a refund (reason customer_request), and receive an email confirmation at bob@example.com. Do all steps in order.",
        "oracle": [("get_customer", {"email": "bob@example.com"}), ("get_order", {"order_id": "ORD-1003"}), ("cancel_order", {"order_id": "ORD-1003"}), ("compute_refund", {"order_id": "ORD-1003", "reason": "customer_request"}), ("send_email", {"to": "bob@example.com", "subject": "Cancellation of ORD-1003", "body": "Order ORD-1003 cancelled. Refund 250.0 USD."})],
        "expected": {"result": {"order_id": "ORD-1003", "status": "cancelled", "refund_amount": rf["refund_amount"]}, "result_mode": "exact",
                     "expected_orders": {"ORD-1003": "cancelled"}, "expected_tickets": 0, "expected_emails": 1,
                     "email_match": {"to": "bob@example.com", "subject_contains": "ORD-1003"}, "minimal_steps": 5},
    })
    # T2 alice summary GBP
    env = MockEnv()
    env.call("get_customer", {"email": "alice@example.com"})
    lo = env.call("list_orders", {"customer_id": "C001"})
    total = round(sum(o["total"] for o in lo["orders"]), 2)
    conv = env.call("convert_currency", {"amount": total, "from": "USD", "to": "GBP"})
    assert lo["ok"] and conv["ok"]
    scenarios.append({
        "sid": "alice_summary_gbp", "tier": "medium",
        "user_request": "Summarise all orders of Alice Anderson (alice@example.com): list them, compute the combined total in USD, and convert that total to GBP.",
        "oracle": [("get_customer", {"email": "alice@example.com"}), ("list_orders", {"customer_id": "C001"}), ("convert_currency", {"amount": total, "from": "USD", "to": "GBP"})],
        "expected": {"result": {"customer_id": "C001", "total_usd": total, "total_gbp": conv["converted"]}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0, "minimal_steps": 3},
    })
    # T3 carla issue
    env = MockEnv()
    env.call("get_customer", {"email": "carla@example.com"})
    env.call("get_order", {"order_id": "ORD-1005"})
    tk = env.call("create_ticket", {"customer_id": "C003", "subject": "Late headphones ORD-1005", "priority": "urgent"})
    env.call("send_email", {"to": "carla@example.com", "subject": "Ticket for ORD-1005", "body": "We created an urgent ticket for your late headphones."})
    assert tk["ok"]
    scenarios.append({
        "sid": "carla_issue", "tier": "medium",
        "user_request": "Carla Costa (carla@example.com) reports that order ORD-1005 (headphones) is late. Check her order, create an urgent ticket, and email her at carla@example.com.",
        "oracle": [("get_customer", {"email": "carla@example.com"}), ("get_order", {"order_id": "ORD-1005"}), ("create_ticket", {"customer_id": "C003", "subject": "Late headphones ORD-1005", "priority": "urgent"}), ("send_email", {"to": "carla@example.com", "subject": "Ticket for ORD-1005", "body": "We created an urgent ticket for your late headphones."})],
        "expected": {"result": {"ticket_id": tk["ticket_id"], "emailed_to": "carla@example.com"}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 1,
                     "ticket_match": {"customer_id": "C003", "priority": "urgent"},
                     "expected_emails": 1, "email_match": {"to": "carla@example.com"}, "minimal_steps": 4},
    })
    # T4 travel
    env = MockEnv()
    w1 = env.call("get_weather", {"city": "London", "unit": "celsius"})
    w2 = env.call("get_weather", {"city": "Paris", "unit": "celsius"})
    cv = env.call("convert_currency", {"amount": 200, "from": "USD", "to": "EUR"})
    assert w1["ok"] and w2["ok"] and cv["ok"]
    scenarios.append({
        "sid": "travel_budget", "tier": "easy",
        "user_request": "I travel to London and Paris. Get the weather in both cities in celsius and convert 200 USD to EUR for my budget.",
        "oracle": [("get_weather", {"city": "London", "unit": "celsius"}), ("get_weather", {"city": "Paris", "unit": "celsius"}), ("convert_currency", {"amount": 200, "from": "USD", "to": "EUR"})],
        "expected": {"result": {"London": w1["temp"], "Paris": w2["temp"], "budget_eur": cv["converted"]}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0, "minimal_steps": 3},
    })
    # T5 dmytro damaged
    env = MockEnv()
    env.call("get_order", {"order_id": "ORD-1007"})
    rf2 = env.call("compute_refund", {"order_id": "ORD-1007", "reason": "damaged"})
    tk2 = env.call("create_ticket", {"customer_id": "C004", "subject": "Damaged monitor ORD-1007", "priority": "high"})
    env.call("send_email", {"to": "dmytro@example.com", "subject": "Refund for ORD-1007", "body": "Refund processed for damaged monitor."})
    assert rf2["ok"] and tk2["ok"]
    scenarios.append({
        "sid": "damaged_monitor", "tier": "hard",
        "user_request": "Order ORD-1007 arrived damaged. Compute the damaged refund, create a high priority ticket for customer C004, and email dmytro@example.com about the refund.",
        "oracle": [("get_order", {"order_id": "ORD-1007"}), ("compute_refund", {"order_id": "ORD-1007", "reason": "damaged"}), ("create_ticket", {"customer_id": "C004", "subject": "Damaged monitor ORD-1007", "priority": "high"}), ("send_email", {"to": "dmytro@example.com", "subject": "Refund for ORD-1007", "body": "Refund processed for damaged monitor."})],
        "expected": {"result": {"refund_amount": rf2["refund_amount"], "ticket_priority": "high"}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 1,
                     "ticket_match": {"customer_id": "C004", "priority": "high"},
                     "expected_emails": 1, "email_match": {"to": "dmytro@example.com"}, "minimal_steps": 4},
    })
    # T6 pending cancel + ticket + email
    env = MockEnv()
    env.call("cancel_order", {"order_id": "ORD-1005"})
    tk3 = env.call("create_ticket", {"customer_id": "C003", "subject": "Cancellation ORD-1005", "priority": "medium"})
    env.call("send_email", {"to": "carla@example.com", "subject": "ORD-1005 cancelled", "body": "Your pending order was cancelled."})
    assert tk3["ok"]
    scenarios.append({
        "sid": "pending_cancel", "tier": "medium",
        "user_request": "Cancel pending order ORD-1005, then create a medium priority ticket for C003 about the cancellation and email carla@example.com.",
        "oracle": [("cancel_order", {"order_id": "ORD-1005"}), ("create_ticket", {"customer_id": "C003", "subject": "Cancellation ORD-1005", "priority": "medium"}), ("send_email", {"to": "carla@example.com", "subject": "ORD-1005 cancelled", "body": "Your pending order was cancelled."})],
        "expected": {"result": {"order_id": "ORD-1005", "status": "cancelled"}, "result_mode": "exact",
                     "expected_orders": {"ORD-1005": "cancelled"}, "expected_tickets": 1,
                     "ticket_match": {"customer_id": "C003", "priority": "medium"},
                     "expected_emails": 1, "email_match": {"to": "carla@example.com"}, "minimal_steps": 3},
    })
    # T7 multi customer
    env = MockEnv()
    a = env.call("list_orders", {"customer_id": "C001"})
    b = env.call("list_orders", {"customer_id": "C002"})
    ta = round(sum(o["total"] for o in a["orders"]), 2)
    ce = env.call("convert_currency", {"amount": ta, "from": "USD", "to": "EUR"})
    assert a["ok"] and b["ok"] and ce["ok"]
    scenarios.append({
        "sid": "multi_customer", "tier": "hard",
        "user_request": "Report how many orders Alice (C001) and Bob (C002) each have, and convert Alice's combined total from USD to EUR.",
        "oracle": [("list_orders", {"customer_id": "C001"}), ("list_orders", {"customer_id": "C002"}), ("convert_currency", {"amount": ta, "from": "USD", "to": "EUR"})],
        "expected": {"result": {"alice_orders": len(a["orders"]), "bob_orders": len(b["orders"]), "alice_total_eur": ce["converted"]}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0, "minimal_steps": 3},
    })
    # T8 summarize no mutation
    env = MockEnv()
    o1 = env.call("get_order", {"order_id": "ORD-1001"})
    o2 = env.call("get_order", {"order_id": "ORD-1002"})
    assert o1["ok"] and o2["ok"]
    scenarios.append({
        "sid": "summarize_orders", "tier": "easy",
        "user_request": "Give the status and total of orders ORD-1001 and ORD-1002. Do not change anything.",
        "oracle": [("get_order", {"order_id": "ORD-1001"}), ("get_order", {"order_id": "ORD-1002"})],
        "expected": {"result": {"ORD-1001": {"status": o1["status"], "total": o1["total"]}, "ORD-1002": {"status": o2["status"], "total": o2["total"]}}, "result_mode": "exact",
                     "expected_orders": {}, "expected_tickets": 0, "expected_emails": 0,
                     "forbid_mutations": True, "minimal_steps": 2},
    })
    assert len(scenarios) == 8
    for s in scenarios:
        e2 = MockEnv()
        for name, args in s["oracle"]:
            r = e2.call(name, args)
            assert r.get("ok"), f"{s['sid']} {name} {r}"
        snap = e2.snapshot()
        for oid, st in s["expected"].get("expected_orders", {}).items():
            assert snap["orders"].get(oid) == st, s["sid"]
        assert len(snap["tickets"]) == s["expected"].get("expected_tickets", 0), s["sid"]
        assert len(snap["sent_emails"]) == s["expected"].get("expected_emails", 0), s["sid"]
    return scenarios


def main() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outdir = os.path.join(root, "fixtures", "HOME-21")
    os.makedirs(outdir, exist_ok=True)
    scenarios = _build_raw()
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
        cid = f"HOME-21-{i+1:02d}"
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
