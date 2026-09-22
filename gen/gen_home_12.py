"""Generator for HOME-12 NuExtract (owner: TASK_B2). Seeded, self-verifying."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

TEST_ID = "HOME-12"
SEED = 121212

T_INVOICE = {
    "invoice_id": "string, invoice number verbatim, e.g. INV-2041",
    "date": "string, invoice date YYYY-MM-DD",
    "vendor": {"name": "string, vendor company name", "city": "string, vendor city"},
    "items": [{"description": "string", "quantity": "number", "price_usd": "number"}],
    "total_usd": "number, invoice total in USD",
    "notes": "string, delivery notes; empty string if not stated",
}
T_EMAIL = {
    "sender": "string, sender name and role",
    "recipient": "string, recipient name",
    "date": "string, email date YYYY-MM-DD",
    "subject": "string, email subject line",
    "action_items": [{"owner": "string", "task": "string", "due": "string YYYY-MM-DD"}],
    "meeting_date": "string, follow-up meeting date YYYY-MM-DD; empty string if none",
}
T_INCIDENT = {
    "incident_id": "string, e.g. INC-3301",
    "date": "string, incident date YYYY-MM-DD",
    "location": "string, site name",
    "reporter": "string, reporter name",
    "systems_affected": ["string, system names"],
    "severity": "string, one of low/medium/high/critical",
    "resolution": "string, resolution summary; empty string if unresolved",
}

EX_INVOICE = {"example_text": "Invoice INV-1000 dated 2026-01-05 from Acme Ltd in Berlin. Item: Widget A, qty 2 at 10 USD. Total 20 USD. Deliver on weekdays.",
              "example_extraction": {"invoice_id": "INV-1000", "date": "2026-01-05",
                                     "vendor": {"name": "Acme Ltd", "city": "Berlin"},
                                     "items": [{"description": "Widget A", "quantity": 2, "price_usd": 10}],
                                     "total_usd": 20, "notes": ""}}
EX_EMAIL = {"example_text": "From: John Lee (Ops) To: Mary Wu Date: 2026-02-01 Subject: Depot visit. Action: John to confirm slots by 2026-02-05. No follow-up meeting.",
            "example_extraction": {"sender": "John Lee (Ops)", "recipient": "Mary Wu", "date": "2026-02-01",
                                   "subject": "Depot visit", "action_items": [{"owner": "John", "task": "confirm slots", "due": "2026-02-05"}],
                                   "meeting_date": ""}}
EX_INCIDENT = {"example_text": "Incident INC-1000 on 2026-03-02 at North Depot reported by Sam Ray. Systems: Scanner S1. Severity: low. Resolved by restart.",
               "example_extraction": {"incident_id": "INC-1000", "date": "2026-03-02", "location": "North Depot",
                                      "reporter": "Sam Ray", "systems_affected": ["Scanner S1"], "severity": "low",
                                      "resolution": "Resolved by restart"}}


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def inv_text(r: dict) -> str:
    items_s = "; ".join(f"{it['description']}, quantity {it['quantity']} at {it['price_usd']} USD each" for it in r["items"])
    notes_s = f" Delivery notes: {r['notes']}." if r["notes"] else " No additional delivery notes were given."
    return (
        f"Commercial invoice {r['invoice_id']} issued on {r['date']} by {r['vendor']['name']}, based in {r['vendor']['city']}. "
        f"This invoice covers the following goods: {items_s}. The total amount due is {r['total_usd']} USD, payable within thirty days of the invoice date. "
        f"The purchasing department confirmed receipt of the order confirmation and matched the line items against the delivery docket from the {r['vendor']['city']} warehouse. "
        f"Payment should reference invoice {r['invoice_id']} so the accounts team can allocate it correctly.{notes_s} "
        f"For questions about this invoice, contact the billing desk of {r['vendor']['name']} during business hours with the invoice number ready. "
        f"The finance system recorded invoice {r['invoice_id']} on {r['date']} for a total of {r['total_usd']} USD including all listed items. "
        f"The warehouse in {r['vendor']['city']} packed the goods on pallets and attached the delivery docket referencing {r['invoice_id']} on every carton. "
        f"The carrier collected the consignment two days after {r['date']} and confirmed that the packaging was intact and properly labelled. "
        f"Upon arrival, the receiving team counted the cartons, checked the goods against invoice {r['invoice_id']}, and signed the handover protocol. "
        f"Any discrepancy must be reported within seven days quoting invoice {r['invoice_id']} and the delivery docket number from {r['vendor']['city']}. "
        f"The accounts payable team of {r['vendor']['name']} reconciles incoming payments every Friday and sends receipts by email.")


def email_text(r: dict) -> str:
    acts = "; ".join(f"{a['owner']} will {a['task']} by {a['due']}" for a in r["action_items"])
    meet = f" A follow-up meeting is scheduled on {r['meeting_date']}." if r["meeting_date"] else " No follow-up meeting was scheduled."
    return (
        f"From: {r['sender']}\nTo: {r['recipient']}\nDate: {r['date']}\nSubject: {r['subject']}\n\n"
        f"Hi {r['recipient'].split()[0]}, following up on our discussion about {r['subject'].lower()}, here is a summary of what we agreed. "
        f"The agreed action items are: {acts}. Please treat the due dates as firm because the downstream plan depends on them. "
        f"We reviewed the open points from last week and closed three of them during the call on {r['date']}.{meet} "
        f"If any of the actions owned by {r['action_items'][0]['owner']} cannot be completed on time, please escalate early so we can replan. "
        f"The background is as follows. Last quarter the team reviewed the process behind {r['subject'].lower()} and agreed on tighter deadlines "
        f"because delays had affected two dependent projects in a row. The department head asked for weekly status updates until everything is green. "
        f"All dates in this email refer to the calendar year 2026 and all owners confirmed their availability for the coming weeks. "
        f"The archive of previous decisions about {r['subject'].lower()} is kept in the shared folder for reference during the next review. "
        f"Thanks for your cooperation on {r['subject'].lower()}, and let me know if I missed anything in this summary. Best regards, {r['sender'].split()[0]}")


def inc_text(r: dict) -> str:
    sys_s = ", ".join(r["systems_affected"])
    res = f" Resolution: {r['resolution']}." if r["resolution"] else " The incident is still unresolved and the team continues to investigate."
    return (
        f"Incident report {r['incident_id']} dated {r['date']} at {r['location']}, reported by {r['reporter']}. "
        f"At approximately 09:40 the monitoring system raised an alert affecting {sys_s}. The on-call engineer rated the severity as {r['severity']} "
        f"because downstream operations at {r['location']} were partially degraded. {r['reporter']} coordinated with the shift lead and recorded each step in the service log.{res} "
        f"A post-incident review for {r['incident_id']} will be scheduled next week at {r['location']} to confirm the fix and update the runbook. "
        f"The response timeline shows that the alert was acknowledged within ten minutes and the specialist arrived on site within the hour. "
        f"Communication during the event went through the group channel so that {r['location']} managers had live updates at all times. "
        f"Spare parts were taken from the {r['location']} storage room and the consumption was recorded in the inventory system. "
        f"All timestamps in this report refer to {r['date']} and all system names were copied from the asset register.")


RECORDS: list[tuple[str, dict, dict, dict]] = [
    ("easy", T_INVOICE, EX_INVOICE, {"invoice_id": "INV-2041", "date": "2026-07-11", "vendor": {"name": "Baltic Parts", "city": "Gdansk"},
     "items": [{"description": "Steel bracket B-40", "quantity": 10, "price_usd": 12}], "total_usd": 120, "notes": ""}),
    ("easy", T_EMAIL, EX_EMAIL, {"sender": "Anna Kowalska (Logistics)", "recipient": "Peter Novak", "date": "2026-08-02",
     "subject": "Quarterly stock count", "action_items": [{"owner": "Anna", "task": "publish count sheet", "due": "2026-08-09"}], "meeting_date": ""}),
    ("easy", T_INCIDENT, EX_INCIDENT, {"incident_id": "INC-3301", "date": "2026-06-15", "location": "North Depot",
     "reporter": "Sam Ray", "systems_affected": ["Conveyor C2"], "severity": "medium", "resolution": "Belt realigned and tested"}),
    ("medium", T_INVOICE, EX_INVOICE, {"invoice_id": "INV-2042", "date": "2026-08-19", "vendor": {"name": "Meridian Supplies", "city": "Brno"},
     "items": [{"description": "Copper cable 50m", "quantity": 4, "price_usd": 45}, {"description": "Junction box J-9", "quantity": 6, "price_usd": 8}],
     "total_usd": 228, "notes": "Leave parcels at reception"}),
    ("medium", T_EMAIL, EX_EMAIL, {"sender": "Tomas Dvorak (Support)", "recipient": "Elena Petrova", "date": "2026-09-01",
     "subject": "Router replacement plan", "action_items": [{"owner": "Tomas", "task": "ship replacement unit", "due": "2026-09-05"},
     {"owner": "Elena", "task": "confirm installation window", "due": "2026-09-06"}], "meeting_date": "2026-09-08"}),
    ("medium", T_INCIDENT, EX_INCIDENT, {"incident_id": "INC-3302", "date": "2026-07-22", "location": "Harbor Warehouse",
     "reporter": "Lena Fischer", "systems_affected": ["Scanner S3", "Label printer L1"], "severity": "high",
     "resolution": "Devices recalibrated by vendor"}),
    ("hard", T_INVOICE, EX_INVOICE, {"invoice_id": "INV-2043", "date": "2026-09-10", "vendor": {"name": "Delta Components", "city": "Lyon"},
     "items": [{"description": "Sensor module SM-2", "quantity": 3, "price_usd": 89}, {"description": "Mounting kit MK-1", "quantity": 3, "price_usd": 15},
     {"description": "Cable set CS-7", "quantity": 1, "price_usd": 22}], "total_usd": 334, "notes": ""}),
    ("hard", T_EMAIL, EX_EMAIL, {"sender": "Marco Rossi (Procurement)", "recipient": "Julie Martin", "date": "2026-09-12",
     "subject": "Supplier audit follow-up", "action_items": [{"owner": "Marco", "task": "send audit report", "due": "2026-09-15"},
     {"owner": "Julie", "task": "approve corrective plan", "due": "2026-09-18"},
     {"owner": "Marco", "task": "book review call", "due": "2026-09-19"}], "meeting_date": ""}),
    ("hard", T_INCIDENT, EX_INCIDENT, {"incident_id": "INC-3303", "date": "2026-08-30", "location": "East Hub",
     "reporter": "Omar Haddad", "systems_affected": ["Sorter S9", "Camera array C4", "UPS U2"], "severity": "critical", "resolution": ""}),
    ("medium", T_INVOICE, EX_INVOICE, {"invoice_id": "INV-2044", "date": "2026-05-28", "vendor": {"name": "Nordwind Trading", "city": "Hamburg"},
     "items": [{"description": "Pallet wrap rolls", "quantity": 20, "price_usd": 6}], "total_usd": 120, "notes": "Deliver before noon"}),
    ("easy", T_EMAIL, EX_EMAIL, {"sender": "Sara Lindqvist (HR)", "recipient": "Jonas Weber", "date": "2026-07-07",
     "subject": "Onboarding schedule", "action_items": [{"owner": "Sara", "task": "send welcome pack", "due": "2026-07-10"}], "meeting_date": "2026-07-14"}),
    ("medium", T_INCIDENT, EX_INCIDENT, {"incident_id": "INC-3304", "date": "2026-09-05", "location": "Central Depot",
     "reporter": "Irina Koval", "systems_affected": ["Dock door D5"], "severity": "low", "resolution": "Hinge lubricated, door tested"}),
]


PAD_SENTS = [
    "The operations manual requires that every record keeps a complete audit trail for later review.",
    "Supervisors check the documentation weekly and sign off on the completed entries.",
    "All timestamps use the local time of the issuing office unless stated otherwise.",
    "Copies of this document are stored in the archive for seven years under the retention schedule.",
]


def _pad(text: str) -> str:
    while len(text) // 4 < 420:
        for s in PAD_SENTS:
            text += " " + s
            if len(text) // 4 >= 420:
                break
    return text


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    dest = root / "fixtures" / TEST_ID
    (dest / "assets").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    items = list(RECORDS)
    rng.shuffle(items)
    by_tier: dict[str, list] = {"easy": [], "medium": [], "hard": []}
    for t, tmpl, ex, rec in items:
        by_tier[t].append((tmpl, ex, rec))
    ordered: list[dict] = []
    for k in range(max(len(v) for v in by_tier.values())):
        for t in ("easy", "medium", "hard"):
            if k < len(by_tier[t]):
                ordered.append((t,) + by_tier[t][k])
    cases = []
    for n, (tier, tmpl, ex, rec) in enumerate(ordered):
        if "invoice_id" in rec:
            text = inv_text(rec)
        elif "incident_id" in rec:
            text = inc_text(rec)
        else:
            text = email_text(rec)
        text = _pad(text)
        toks = len(text) // 4
        assert 400 <= toks <= 1500, f"text tokens ~{toks}"
        # verify verbatim leaves
        for path, val in flatten(rec).items():
            if val == "" or val is None:
                continue
            assert str(val) in text, f"{path}={val!r} not verbatim in case {n}"
        cases.append({"id": f"H12-{n+1:03d}", "test_id": TEST_ID, "tier": tier, "lang": "en",
                      "input": {"template": tmpl, "example": ex, "text": text},
                      "expected": rec, "meta": {"seed": SEED}})
    with open(dest / "cases.jsonl", "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    files = {"cases.jsonl": _sha256_file(dest / "cases.jsonl")}
    for p in sorted((dest / "assets").rglob("*")):
        if p.is_file():
            files["assets/" + p.relative_to(dest / "assets").as_posix()] = _sha256_file(p)
    with open(dest / "manifest.json", "w", encoding="utf-8") as f:
        json.dump({"test_id": TEST_ID, "version": "n1", "seed": SEED, "files": files},
                  f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
