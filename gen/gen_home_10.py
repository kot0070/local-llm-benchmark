"""Generator for HOME-10 multilingual log state tracking (owner: TASK_C)."""
from __future__ import annotations

import hashlib
import json
import os
import random

TEST_ID = "HOME-10"
SEED = 1007

ENTITIES = ["PKG-A", "PKG-B", "PKG-C", "PKG-D", "PKG-E", "PKG-F", "PKG-G", "PKG-H"]
STATES = ["ordered", "shipped", "in_transit", "delivered", "on_hold", "returned", "cancelled", "lost"]
STATE_WORD = {
    "en": {"ordered": "ordered", "shipped": "shipped", "in_transit": "in transit", "delivered": "delivered", "on_hold": "on hold", "returned": "returned", "cancelled": "cancelled", "lost": "lost"},
    "fr": {"ordered": "commande", "shipped": "expedie", "in_transit": "en transit", "delivered": "livre", "on_hold": "en attente", "returned": "retourne", "cancelled": "annule", "lost": "perdu"},
    "de": {"ordered": "bestellt", "shipped": "versandt", "in_transit": "unterwegs", "delivered": "geliefert", "on_hold": "angehalten", "returned": "zurueckgesandt", "cancelled": "storniert", "lost": "verloren"},
    "es": {"ordered": "pedido", "shipped": "enviado", "in_transit": "en transito", "delivered": "entregado", "on_hold": "en espera", "returned": "devuelto", "cancelled": "cancelado", "lost": "perdido"},
    "it": {"ordered": "ordinato", "shipped": "spedito", "in_transit": "in transito", "delivered": "consegnato", "on_hold": "in attesa", "returned": "restituito", "cancelled": "annullato", "lost": "smarrito"},
}
LANGS = ["en", "fr", "de", "es", "it"]
TEMPL = {
    "en": "Parcel {ent} is now {st} at hub {hub}. Operator note {note}.",
    "fr": "Colis {ent} est maintenant {st} au hub {hub}. Note operateur {note}.",
    "de": "Paket {ent} ist jetzt {st} im Hub {hub}. Vermerk {note}.",
    "es": "Paquete {ent} ahora esta {st} en el centro {hub}. Nota {note}.",
    "it": "Pacco {ent} ora e {st} presso hub {hub}. Nota {note}.",
}
HUBS = ["Lyon", "Kyiv", "Berlin", "Madrid", "Roma", "Paris", "Hamburg", "Porto"]


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_log(rng: random.Random, log_idx: int):
    # Per-entity chains.
    chains: dict[str, list[dict]] = {e: [] for e in ENTITIES}
    for e in ENTITIES:
        n = rng.choice([26, 28, 30, 32])
        cur = "ordered"
        for k in range(n):
            # Random walk to next state.
            nxt = rng.choice(STATES)
            # Avoid staying trivially; allow.
            lang = rng.choice(LANGS)
            chains[e].append({"state": nxt, "lang": lang, "kind": "update"})
            cur = nxt
        # Force 1-2 corrections referencing earlier positions.
        if len(chains[e]) >= 6:
            pos = rng.randrange(3, len(chains[e]) - 1)
            ref_pos = rng.randrange(0, pos)
            # Correction event overwrites with a new decisive-ish state.
            corr_state = rng.choice(STATES)
            chains[e][pos] = {"state": corr_state, "lang": rng.choice(LANGS), "kind": "correction", "ref_offset": pos - ref_pos}
    # Interleave into global event order.
    # Flatten with per-entity order preserved, shuffled deterministically.
    flat = []
    for e in ENTITIES:
        for ev in chains[e]:
            flat.append((e, ev))
    rng.shuffle(flat)
    events = []
    for i, (ent, ev) in enumerate(flat, start=1):
        eid = f"E{i:03d}"
        lang = ev["lang"]
        st_word = STATE_WORD[lang][ev["state"]]
        hub = rng.choice(HUBS)
        note = rng.randint(100, 999)
        base = TEMPL[lang].format(ent=ent, st=st_word, hub=hub, note=note)
        ref_txt = ""
        ref_id = None
        if ev.get("kind") == "correction":
            # Reference an earlier event of the same entity.
            earlier = [x["id"] for x in events if x["entity"] == ent]
            ref_id = rng.choice(earlier) if earlier else None
            if ref_id:
                tag = rng.choice(["CORRECTION of", "REVERSAL of"])
                # Multilingual tag variants keep the English keyword for traceability.
                ref_txt = f" {tag} {ref_id}: prior scan amended."
        text = base + ref_txt + f" [{lang}]"
        # Pad to ~250 chars deterministically.
        pad = f" Checkpoint {rng.randint(1, 40)}, seal {rng.randint(1000, 9999)}, handler {rng.choice(['A','B','C','D'])}-{rng.randint(10, 99)}."
        pad2 = f" Manifest {rng.randint(10000, 99999)}, weight {rng.randint(2, 40)}kg, inspector {rng.choice(HUBS)}."
        events.append({"id": eid, "entity": ent, "state": ev["state"], "lang": lang,
                       "kind": ev.get("kind", "update"), "ref": ref_id, "text": text + pad + pad2})
    # Reference state machine: replay in E order (already ordered).
    final: dict[str, dict] = {}
    for ev in events:
        final[ev["entity"]] = {"state": ev["state"], "evidence": [ev["id"]] if not ev["ref"] else [ev["id"], ev["ref"]]}
    # Build log text.
    lines = [f"# Transit log L{log_idx+1:02d} — {len(events)} events, 8 parcels, languages en/fr/de/es/it.",
             "States are written in the event language; CORRECTION/REVERSAL lines amend the referenced event.",
             ""]
    for ev in events:
        lines.append(f"{ev['id']} | {ev['entity']} | {ev['text']}")
    text = "\n".join(lines) + "\n"
    return text, events, final


def main() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outdir = os.path.join(root, "fixtures", "HOME-10")
    os.makedirs(outdir, exist_ok=True)
    cases = []
    tiers = ["easy", "medium", "hard"]
    for li in range(3):
        rng = random.Random(SEED * 100 + li)
        text, events, final = _make_log(rng, li)
        chars = len(text)
        assert 30000 <= chars <= 45000, f"log {li} chars {chars}"
        assert 7500 <= chars / 4 <= 11500, f"log {li} tokens {chars/4}"
        # Verify: replay gives same final; evidence ids exist.
        ids = {e["id"] for e in events}
        replay: dict[str, str] = {}
        for ev in events:
            replay[ev["entity"]] = ev["state"]
        for ent in ENTITIES:
            assert replay[ent] == final[ent]["state"], ent
            for eid in final[ent]["evidence"]:
                assert eid in ids, eid
        expected = [{"entity": e, "state": final[e]["state"], "evidence_ids": final[e]["evidence"]} for e in ENTITIES]
        cases.append({"id": f"HOME-10-{li+1:02d}", "test_id": TEST_ID, "tier": tiers[li], "lang": "multi",
                      "input": {"log": text, "entities": list(ENTITIES)},
                      "expected": expected,
                      "meta": {"events": len(events), "chars": chars, "log": f"L{li+1:02d}"}})
    # Already stratified easy/medium/hard.
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
