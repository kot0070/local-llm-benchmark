"""Generator for HOME-09 long-context wiki QA (owner: TASK_C)."""
from __future__ import annotations

import hashlib
import json
import os
import random

TEST_ID = "HOME-09"
SEED = 907

DEPTS = ["Logistics", "Optics", "Power Systems", "Thermal Lab", "Field Ops", "Data Platform",
         "Materials", "Avionics", "Comms", "Safety", "Robotics", "Hydro"]
TOPICS = ["intake checklist", "calibration log", "shift handover", "vendor notes", "test report",
          "maintenance window", "inventory audit", "deployment guide", "review minutes", "runbook"]
FIRST = ["Amara", "Boris", "Celia", "Dario", "Elif", "Farid", "Greta", "Hugo", "Iris", "Jonas",
         "Kira", "Leon", "Mira", "Nadia", "Omar", "Petra", "Quinn", "Rosa", "Stefan", "Tara"]
LAST = ["Vance", "Kowalski", "Merritt", "Okafor", "Lindqvist", "Barros", "Haddad", "Novak", "Petrov", "Sorensen"]
PLACES = ["Harbor House", "North Annex", "Kestrel Hall", "Vulcan Wing", "Maple Depot", "Cinder Block",
          "Lumen Tower", "Granite Vault", "Willow Shed", "Cobalt Yard", "Amber Atrium", "Frost Gate"]
PROJECTS = ["Skylark", "Ferrostat", "Lumenarc", "Driftline", "Cobalt Ferry", "Heliotrope", "Vantacore", "Mistralith"]
DEVICES = ["Relay K7", "Pump P12", "Sensor Array S9", "Valve V4", "Converter C3", "Beacon B6", "Filter F2", "Motor M8"]
COMPS = ["flux gasket", "ceramic shim", "torque collar", "phase coil", "seal ring", "bias plate", "mesh screen", "drive belt"]
WARES = ["Depot East", "Vault 3", "Shed 7", "Annex 2", "Yard North", "Store Beta", "Lockup 9", "Hold Gamma"]


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_doc(rng: random.Random, doc_idx: int):
    # Pick hop facts.
    proj = PROJECTS[(doc_idx * 2) % len(PROJECTS)]
    proj_sim = PROJECTS[(doc_idx * 2 + 1) % len(PROJECTS)]
    person = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    person_old = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    office = PLACES[(doc_idx * 3) % len(PLACES)]
    office_old = PLACES[(doc_idx * 3 + 1) % len(PLACES)]
    device = DEVICES[(doc_idx * 2) % len(DEVICES)]
    comp = COMPS[(doc_idx * 2) % len(COMPS)]
    ware = WARES[(doc_idx * 2) % len(WARES)]
    ware_old = WARES[(doc_idx * 2 + 1) % len(WARES)]
    # Distant section indices (1-based).
    a1, b1 = 18 + doc_idx, 97 - doc_idx
    a2, b2 = 41 + doc_idx, 112 - doc_idx
    while len({a1, b1, a2, b2}) < 4:
        b2 -= 1
    facts = {
        "proj": proj, "proj_sim": proj_sim, "person": person, "person_old": person_old,
        "office": office, "office_old": office_old, "device": device, "comp": comp,
        "ware": ware, "ware_old": ware_old, "a1": a1, "b1": b1, "a2": a2, "b2": b2,
    }
    sections = []
    for i in range(1, 121):
        sid = f"S{i:03d}"
        dept = rng.choice(DEPTS)
        topic = rng.choice(TOPICS)
        title = f"{dept} — {topic} ({sid})"
        body = _section_body(rng, i, facts)
        sections.append((sid, title, body))
    # Build text.
    parts = [f"# Halcyon Works — site wiki (doc D{doc_idx+1:02d})",
             f"This wiki has 120 sections (S001..S120). Values marked 'superseded' are outdated; only current values count.",
             ""]
    for sid, title, body in sections:
        parts.append(f"## {sid} — {title}\n{body}\n")
    text = "\n".join(parts)
    return text, sections, facts


def _section_body(rng: random.Random, i: int, facts: dict) -> str:
    # Inject hop facts + distractors at chosen sections.
    if i == facts["a1"]:
        return (f"Project {facts['proj']} is currently led by {facts['person']}. "
                f"Earlier this year it was led by {facts['person_old']} (superseded). "
                f"Do not confuse with Project {facts['proj_sim']}, which is led by {facts['person_old']}. "
                f"The team meets weekly and files intake checklists on Fridays. "
                f"Budget code updated last quarter; see finance annex for details.")
    if i == facts["b1"]:
        return (f"{facts['person']} works in office {facts['office']}. "
                f"Previously {facts['person']} sat in {facts['office_old']} (superseded). "
                f"{facts['person_old']} still sits in {facts['office_old']}. "
                f"Access badges are issued at the front desk between 8 and 17. "
                f"Desk moves are frozen during audit weeks.")
    if i == facts["a2"]:
        return (f"Device {facts['device']} uses one {facts['comp']} in its main assembly. "
                f"An older revision used a mesh screen (superseded). "
                f"Inspection of {facts['device']} happens every 90 days. "
                f"Spare {facts['comp']} units are tracked by serial number. "
                f"Torque settings are logged after each service.")
    if i == facts["b2"]:
        return (f"The {facts['comp']} is stored in {facts['ware']}. "
                f"It was previously kept in {facts['ware_old']} (superseded). "
                f"Stock counts for {facts['ware']} are reconciled monthly. "
                f"Transfers out of {facts['ware_old']} require a supervisor sign-off. "
                f"Labels must show the revision letter clearly.")
    # Generic filler: 4-6 sentences, ~450-550 chars.
    sents = []
    n = rng.choice([4, 5, 5, 6])
    for _ in range(n):
        kind = rng.randrange(6)
        if kind == 0:
            sents.append(f"The {rng.choice(['pump','relay','valve','sensor','beacon','filter'])} passed its {rng.choice(['pressure','thermal','vibration','humidity'])} check with margin {rng.randint(3, 18)} percent.")
        elif kind == 1:
            sents.append(f"{rng.choice(FIRST)} {rng.choice(LAST)} filed the {rng.choice(TOPICS)} and flagged {rng.randint(0, 3)} follow-up items for {rng.choice(DEPTS).lower()}.")
        elif kind == 2:
            sents.append(f"Inventory at {rng.choice(WARES)} shows {rng.randint(20, 400)} units of {rng.choice(COMPS)} with revision {rng.choice(['A','B','C','D'])}.")
        elif kind == 3:
            sents.append(f"Shift handover notes mention {rng.choice(DEVICES)} running {rng.randint(40, 99)} percent load with coolant at {rng.randint(18, 34)} degrees.")
        elif kind == 4:
            sents.append(f"Vendor {rng.choice(['Helix','Norvik','Ostram','Peldo','Quartzline'])} quoted {rng.randint(120, 2400)} credits with delivery in {rng.randint(2, 12)} weeks.")
        else:
            sents.append(f"Safety walk on level {rng.randint(1, 6)} found {rng.choice(['clear aisles','tagged valves','charged extinguishers','lit exit signs'])} and one minor spill near {rng.choice(PLACES)}.")
    # Pad to reach target length deterministically.
    extra = f" Reference {rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}; contact the {rng.choice(DEPTS).lower()} desk for clarifications."
    return " ".join(sents) + extra


def main() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outdir = os.path.join(root, "fixtures", "HOME-09")
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(SEED)
    all_cases = []
    tiers = ["easy", "medium", "hard", "easy", "medium", "hard", "easy", "medium"]
    ti = 0
    for d in range(4):
        drng = random.Random(SEED * 100 + d)
        text, sections, facts = _make_doc(drng, d)
        chars = len(text)
        assert chars / 4 <= 16500, f"doc {d} too long: {chars} chars"
        assert 48000 <= chars <= 66000, f"doc {d} off target: {chars}"
        sec_ids = {s for s, _, _ in sections}
        a1, b1, a2, b2 = facts["a1"], facts["b1"], facts["a2"], facts["b2"]
        # Questions.
        q1 = f"Where is the office of the lead of Project {facts['proj']}?"
        e1 = {"answer": facts["office"], "evidence": [f"S{a1:03d}", f"S{b1:03d}"]}
        q2 = f"In which warehouse is the {facts['comp']} used by {facts['device']} stored?"
        e2 = {"answer": facts["ware"], "evidence": [f"S{a2:03d}", f"S{b2:03d}"]}
        # Ground-truth verification.
        for q, e in ((q1, e1), (q2, e2)):
            assert e["answer"] and isinstance(e["answer"], str)
            for sid in e["evidence"]:
                assert sid in sec_ids, sid
            # Answer appears in one evidence section text.
            blob = "\n".join(b for s, _, b in sections if s in set(e["evidence"]))
            assert e["answer"] in blob, f"answer {e['answer']!r} not in evidence"
            assert q and "?" in q
        for q, e in ((q1, e1), (q2, e2)):
            tier = tiers[ti % len(tiers)]
            ti += 1
            cid = f"HOME-09-{len(all_cases)+1:02d}"
            all_cases.append({"id": cid, "test_id": TEST_ID, "tier": tier, "lang": "en",
                              "input": {"document": text, "question": q, "doc_id": f"D{d+1:02d}"},
                              "expected": e, "meta": {"doc": f"D{d+1:02d}", "chars": chars}})
    # Stratified interleave easy/medium/hard.
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for c in all_cases:
        by_tier[c["tier"]].append(c)
    for v in by_tier.values():
        v.sort(key=lambda x: x["id"])
    order = []
    idx = {"easy": 0, "medium": 0, "hard": 0}
    cycle = ["easy", "medium", "hard"]
    ci = 0
    while len(order) < len(all_cases):
        placed = False
        for _ in range(3):
            t = cycle[ci % 3]
            ci += 1
            if idx[t] < len(by_tier[t]):
                order.append(by_tier[t][idx[t]])
                idx[t] += 1
                placed = True
                break
        if not placed:
            break
    # Re-id in stratified order to keep fixture order stratified.
    for i, c in enumerate(order):
        c["id"] = f"HOME-09-{i+1:02d}"
    cpath = os.path.join(outdir, "cases.jsonl")
    with open(cpath, "w", encoding="utf-8", newline="\n") as f:
        for c in order:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    files = {}
    for fn in sorted(os.listdir(outdir)):
        if fn == "manifest.json":
            continue
        files[fn] = _sha256_file(os.path.join(outdir, fn))
    manifest = {"test_id": TEST_ID, "seed": SEED, "n_cases": len(order), "files": files}
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return outdir


if __name__ == "__main__":
    print(main())
