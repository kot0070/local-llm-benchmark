"""Generator for HOME-03 RAG (owner: TASK_B2). Seeded, self-verifying."""
from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

TEST_ID = "HOME-03"
SEED = 30303

FILLER = [
    "Helios Home Goods serves residential customers across three regions with a focus on durable appliances and transparent service terms.",
    "All policy documents are versioned and the version with the latest effective date supersedes earlier versions in case of conflict.",
    "Customer support operates on weekdays from eight to eighteen and provides written confirmation for every approved request.",
    "Product specifications are verified by the quality team before publication and include dimensions, power ratings and warranty coverage.",
    "Contact details for regional offices are listed at the end of each document for escalation and verification purposes.",
    "Returns are inspected at the central warehouse before any refund is issued to the original payment method.",
    "The company updates its price list quarterly and honors the price shown on the order confirmation for thirty days.",
    "Employees follow the documented handling procedure and record each step in the service log for audit purposes.",
    "Seasonal promotions cannot be combined with clearance discounts unless the policy document explicitly allows stacking.",
    "Delivery timeframes depend on stock availability at the nearest depot and on the selected shipping tier.",
]

CASE_SPECS = [
    # direct
    {"kind": "direct", "q": "What is the standard return window for small appliances?",
     "answer": "30 days", "facts": ["30 day"], "cite_count": 1, "topic": "returns"},
    {"kind": "direct", "q": "What is the warranty period for the Helios Air Fryer AF-200?",
     "answer": "2 years", "facts": ["2 year"], "cite_count": 1, "topic": "warranty"},
    {"kind": "direct", "q": "What is the customer support phone number for the North region?",
     "answer": "+1-555-0142", "facts": ["+1-555-0142"], "cite_count": 1, "topic": "contact"},
    {"kind": "direct", "q": "What is the maximum weight for standard parcel delivery?",
     "answer": "25 kg", "facts": ["25 kg"], "cite_count": 1, "topic": "delivery"},
    {"kind": "direct", "q": "What discount applies to energy-efficient models during the spring sale?",
     "answer": "15%", "facts": ["15%"], "cite_count": 1, "topic": "promo"},
    {"kind": "direct", "q": "How many days does a refund to the original payment method take?",
     "answer": "5 business days", "facts": ["5 business day"], "cite_count": 1, "topic": "refund"},
    {"kind": "direct", "q": "What is the power rating of the Helios Kettle EK-150?",
     "answer": "1500 W", "facts": ["1500 w"], "cite_count": 1, "topic": "spec"},
    # synthesis (2 docs)
    {"kind": "synth", "q": "What is the price of the Helios Vacuum HV-90 and its warranty period?",
     "answer": "The Helios Vacuum HV-90 costs 189 USD and includes a 3-year warranty.",
     "facts": ["189 usd", "3 year"], "cite_count": 2, "topic": "price_warranty"},
    {"kind": "synth", "q": "What are the support hours on weekdays and the escalation email?",
     "answer": "Support hours are 8:00-18:00 on weekdays and escalation email is care@helios.example.",
     "facts": ["8:00", "18:00", "care@helios.example"], "cite_count": 2, "topic": "hours_contact"},
    {"kind": "synth", "q": "What is the extended warranty cost for the AF-200 and where is it serviced?",
     "answer": "Extended warranty for AF-200 costs 29 USD and service is at the Central Depot.",
     "facts": ["29 usd", "central depot"], "cite_count": 2, "topic": "extw"},
    # conflicting (newer wins)
    {"kind": "conflict", "q": "What is the current restocking fee for opened items?",
     "answer": "5%", "facts": ["5%"], "cite_count": 1, "topic": "restock"},
    {"kind": "conflict", "q": "What is the current free-shipping threshold?",
     "answer": "75 USD", "facts": ["75 usd"], "cite_count": 1, "topic": "shipping"},
    {"kind": "conflict", "q": "How many days is the price-match guarantee valid?",
     "answer": "14 days", "facts": ["14 day"], "cite_count": 1, "topic": "pricematch"},
    # unanswerable
    {"kind": "unanswerable", "q": "What is the CEO's personal mobile number?",
     "answer": None, "facts": [], "cite_count": 0, "topic": "ceo"},
    {"kind": "unanswerable", "q": "Does Helios sell outdoor swimming pools?",
     "answer": None, "facts": [], "cite_count": 0, "topic": "pools"},
    {"kind": "unanswerable", "q": "What was the company's revenue in 2019?",
     "answer": None, "facts": [], "cite_count": 0, "topic": "revenue"},
]

TIERS = ["easy"] * 6 + ["medium"] * 6 + ["hard"] * 4


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def pad_to_words(text: str, rng: random.Random, lo: int = 250, hi: int = 340) -> str:
    words = text.split()
    fi = 0
    pool = FILLER[:]
    rng.shuffle(pool)
    while len(words) < lo:
        words += pool[fi % len(pool)].split()
        fi += 1
    # trim to hi
    if len(words) > hi:
        words = words[:hi]
    # reflow into paragraphs
    paras = []
    idx = 0
    while idx < len(words):
        paras.append(" ".join(words[idx:idx + 55]))
        idx += 55
    return "\n\n".join(paras)


def make_case(i: int, spec: dict, tier: str, rng: random.Random) -> dict:
    n_docs = 6 + (i % 5)  # 6..10
    docs: list[dict] = []
    answer = spec["answer"]
    kind = spec["kind"]
    topic = spec["topic"]
    eff_old, eff_new = "2025-06-01", "2026-08-15"
    cite_ids: list[str] = []

    if kind == "unanswerable":
        for d in range(n_docs):
            title = f"Helios policy note {topic}-{i}-{d}"
            body = (f"Document D{d+1}: {title}. Effective date {eff_old}. " +
                    f"This note covers {topic} general procedures for Helios Home Goods staff. " +
                    "It describes intake, logging and internal review steps without disclosing private data. ")
            docs.append({"id": f"D{d+1}", "title": title, "effective_date": eff_old,
                         "text": pad_to_words(body, rng)})
        expected = {"answer": None, "citations": [], "abstain": True, "facts": []}
    elif kind == "conflict":
        # D1 old value, D2 new value (winner); rest distractors
        old_val = {"restock": "10%", "shipping": "50 USD", "pricematch": "7 days"}[topic]
        new_val = answer
        t_old = f"Policy on {topic}. Effective date {eff_old}. The applicable value is {old_val}. Staff must apply this rate to all requests received before the update."
        t_new = f"Policy on {topic} (revised). Effective date {eff_new}. This revision supersedes all earlier versions. The applicable value is now {new_val}. Staff must apply the revised value to all requests."
        docs.append({"id": "D1", "title": f"{topic} policy v1", "effective_date": eff_old, "text": pad_to_words(t_old, rng)})
        docs.append({"id": "D2", "title": f"{topic} policy v2", "effective_date": eff_new, "text": pad_to_words(t_new, rng)})
        for d in range(2, n_docs):
            docs.append({"id": f"D{d+1}", "title": f"{topic} appendix {d}", "effective_date": eff_old,
                         "text": pad_to_words(f"Document D{d+1}: appendix on {topic} procedures. Effective date {eff_old}. General guidance for staff handling.", rng)})
        cite_ids = ["D2"]
        expected = {"answer": answer, "citations": cite_ids, "abstain": False, "facts": spec["facts"]}
    elif kind == "synth":
        parts = {
            "price_warranty": ("The Helios Vacuum HV-90 costs 189 USD according to the autumn price list effective 2026-09-01.",
                               "The Helios Vacuum HV-90 includes a 3-year warranty serviced under standard terms effective 2026-09-01."),
            "hours_contact": ("Customer support hours are 8:00-18:00 on weekdays at all Helios offices effective 2026-01-10.",
                              "Escalation contact is care@helios.example for unresolved cases effective 2026-01-10."),
            "extw": ("Extended warranty for the AF-200 costs 29 USD for one additional year effective 2026-05-20.",
                     "Warranty service for the AF-200 is performed at the Central Depot effective 2026-05-20."),
        }[topic]
        docs.append({"id": "D1", "title": f"{topic} part A", "effective_date": "2026-09-01",
                     "text": pad_to_words(f"Document D1: {parts[0]} Details below for staff and customers.", rng)})
        docs.append({"id": "D2", "title": f"{topic} part B", "effective_date": "2026-09-01",
                     "text": pad_to_words(f"Document D2: {parts[1]} Details below for staff and customers.", rng)})
        for d in range(2, n_docs):
            docs.append({"id": f"D{d+1}", "title": f"{topic} note {d}", "effective_date": "2026-01-10",
                         "text": pad_to_words(f"Document D{d+1}: background note on {topic} operations. General staff guidance.", rng)})
        cite_ids = ["D1", "D2"]
        expected = {"answer": answer, "citations": cite_ids, "abstain": False, "facts": spec["facts"]}
    else:  # direct
        key_sentence = {
            "returns": f"The standard return window for small appliances is {answer} from delivery, per policy effective 2026-07-01.",
            "warranty": f"The Helios Air Fryer AF-200 carries a warranty period of {answer} under normal household use, effective 2026-03-01.",
            "contact": f"Customers in the North region can reach support at {answer} on weekdays, effective 2026-02-01.",
            "delivery": f"Standard parcel delivery accepts items up to {answer} per parcel, effective 2026-04-15.",
            "promo": f"Energy-efficient models receive a {answer} discount during the spring sale, effective 2026-04-01.",
            "refund": f"Refunds to the original payment method are completed within {answer} after warehouse inspection, effective 2026-06-10.",
            "spec": f"The Helios Kettle EK-150 has a rated power of {answer} at 220 V, effective 2026-01-20.",
        }[topic]
        anchor = 1 + (i % (n_docs - 1))
        for d in range(n_docs):
            did = f"D{d+1}"
            if d + 1 == anchor:
                body = f"Document {did}: {topic} reference. Effective date 2026-07-01. {key_sentence} The following sections explain procedure and contacts."
                cite_ids = [did]
            else:
                body = f"Document {did}: background note on {topic} operations. Effective date 2026-01-10. General staff guidance and related procedures."
            docs.append({"id": did, "title": f"{topic} doc {d+1}", "effective_date": "2026-07-01" if d + 1 == anchor else "2026-01-10",
                         "text": pad_to_words(body, rng)})
        expected = {"answer": answer, "citations": cite_ids, "abstain": False, "facts": spec["facts"]}

    # enforce total size <= 5500 tokens (~4 chars/token => 22000 chars)
    total_chars = sum(len(d["text"]) for d in docs)
    assert total_chars <= 22000, f"case {i} too big: {total_chars}"
    for d in docs:
        wc = len(d["text"].split())
        assert 200 <= wc <= 420, f"doc {d['id']} words={wc}"

    # verification
    if expected["answer"] is None:
        assert expected["abstain"] is True and expected["citations"] == []
        assert expected["facts"] == []
    else:
        assert expected["abstain"] is False
        assert isinstance(expected["facts"], list) and len(expected["facts"]) >= 1
        ans = expected["answer"]
        # every required fact must appear in the cited docs (normalized, units aware)
        cited_text = " ".join(d["text"] for d in docs if d["id"] in expected["citations"])
        import unicodedata as _u
        def _nf(s):
            s = _u.normalize("NFKC", s).casefold()
            s = s.replace("-", " ").replace("_", " ").replace("/", " ")
            s = re.sub(r"\s+", " ", s).strip()
            s = re.sub(r"\byears\b", "year", s)
            s = re.sub(r"\bdays\b", "day", s)
            s = re.sub(r"\bdollars?\b", "usd", s)
            s = s.replace("$", " usd ")
            return re.sub(r"\s+", " ", s).strip()
        def _fact_in(fact, text):
            nf, nt = _nf(str(fact)), _nf(str(text))
            if nf and nf in nt:
                return True
            try:
                m = re.search(r"\d+(?:\.\d+)?", str(fact))
                if m:
                    fv = float(m.group(0))
                    for am in re.finditer(r"\d+(?:\.\d+)?", str(text)):
                        if abs(float(am.group(0)) - fv) < 1e-9:
                            rest = re.sub(r"\d+(?:\.\d+)?", " ", nf).strip()
                            toks = [t for t in re.split(r"\s+", rest) if t and t not in ("-",)]
                            if not toks or all(t in nt for t in toks):
                                return True
            except Exception:
                pass
            return False
        for fact in expected["facts"]:
            assert _fact_in(fact, cited_text), f"fact {fact!r} not grounded case {i}"
        # full answer should also contain its facts
        for fact in expected["facts"]:
            assert _fact_in(fact, ans), f"fact {fact!r} not in answer case {i}"
        for cid in expected["citations"]:
            assert any(d["id"] == cid for d in docs), cid

    cid = f"H03-{i+1:03d}"
    return {"id": cid, "test_id": TEST_ID, "tier": tier, "lang": "en",
            "input": {"question": spec["q"], "documents": docs},
            "expected": expected,
            "meta": {"kind": kind, "seed": SEED}}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    dest = root / "fixtures" / TEST_ID
    (dest / "assets").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    order = list(range(len(CASE_SPECS)))
    # assign tiers then interleave stratified
    specs = [(CASE_SPECS[i], TIERS[i]) for i in order]
    by_tier: dict[str, list] = {"easy": [], "medium": [], "hard": []}
    for idx, (sp, t) in enumerate(specs):
        by_tier[t].append((idx, sp))
    for v in by_tier.values():
        rng.shuffle(v)
    ordered: list[dict] = []
    for k in range(max(len(v) for v in by_tier.values())):
        for t in ("easy", "medium", "hard"):
            if k < len(by_tier[t]):
                idx, sp = by_tier[t][k]
                ordered.append(make_case(idx, sp, t, random.Random(SEED + idx)))
    with open(dest / "cases.jsonl", "w", encoding="utf-8") as f:
        for c in ordered:
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
