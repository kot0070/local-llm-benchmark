"""HOME-10 multilingual log state tracking (owner: TASK_C)."""
from __future__ import annotations

import json
import os

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-10", version="n1", title="Multilingual log state tracking", family="LONG",
            home="mistral-nemo:12b", kind="chat", mode="R0", requires=["text"],
            num_predict=1024, think_extra=2048, num_ctx=16384, timeout_s=1500,
            core_n=2, empty_ok=False)

STATES = ["ordered", "shipped", "in_transit", "on_hold", "delivered", "returned", "lost", "cancelled"]
CONTRACT = ("Respond with ONLY a JSON array like "
            '[{"entity": "<entity id>", "state": "<state>", "evidence_ids": ["<event id>", "<event id>"]}] '
            "(ids are quoted strings) and nothing else. One entry per entity. "
            "state must be exactly one of: " + ", ".join(STATES) + ".")


def load_cases(fixtures_dir: str) -> list[Case]:
    path = os.path.join(fixtures_dir, "cases.jsonl")
    cases: list[Case] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-10"), tier=d.get("tier", ""),
                              lang=d.get("lang", "en"), input=d.get("input", {}),
                              expected=d.get("expected", []), meta=d.get("meta", {})))
    return cases


def build_request(case: Case, profile: Profile) -> Request:
    log = case.input.get("log", "")
    entities = case.input.get("entities", [])
    content = (f"Event log (multiple languages, ids E001...; CORRECTION/REVERSAL lines amend earlier events):\n\n"
               f"{log}\n\nEntities to report: {', '.join(entities)}\n\n{CONTRACT}")
    msgs = []
    if getattr(profile, "system", None):
        msgs.append({"role": "system", "content": profile.system})
    msgs.append({"role": "user", "content": content})
    return Request(endpoint="chat", messages=msgs)


def _norm(s) -> str:
    try:
        from bench.validate.textmetrics import norm_text
        return norm_text(s)
    except Exception:
        import unicodedata
        return " ".join(unicodedata.normalize("NFKC", str(s)).casefold().split())


def _ev_f1(got, exp) -> float:
    def n(xs):
        s = set()
        for x in (xs or []):
            if isinstance(x, str):
                s.add(x.strip().upper())
        return s
    g, e = n(got), n(exp)
    if not g and not e:
        return 1.0
    if not g or not e:
        return 0.0
    tp = len(g & e)
    prec = tp / len(g)
    rec = tp / len(e)
    return 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    from bench.validate.jsonx import extract_json
    text = resp.content or ""
    exp_list = case.expected or []
    exp_map = {str(e.get("entity", "")).strip().casefold(): e for e in exp_list if isinstance(e, dict)}
    obj, info = extract_json(text)
    broken = bool(info.get("fenced") or info.get("prose"))
    rows = obj if isinstance(obj, list) else None
    if rows is None:
        details = {"n_entities": len(exp_map), "n_got": 0, "per_entity": {},
                   "evidence_f1_mean": 0.0, "fenced": bool(info.get("fenced")),
                   "prose": bool(info.get("prose")), "strict_json": bool(info.get("strict"))}
        return Verdict(status="FORMAT_ERROR", sub_reason="NO_JSON", sem=0.0, strict=0.0,
                       details=details, attribution="MODEL")
    got_map: dict = {}
    for r in rows:
        if isinstance(r, dict) and isinstance(r.get("entity"), str):
            got_map[r["entity"].strip().casefold()] = r
        elif isinstance(r, dict):
            # Non-string entity -> contract broken but keep for scoring.
            broken = True
    n = len(exp_map)
    correct = 0
    f1s = []
    per = {}
    for key, exp in exp_map.items():
        got = got_map.get(key)
        exp_state = _norm(str(exp.get("state", ""))).replace("_", " ").replace("-", " ")
        if got is None:
            per[key] = {"ok": False, "missing": True, "evidence_f1": 0.0}
            f1s.append(0.0)
            continue
        got_state = " ".join(_norm(str(got.get("state", ""))).replace("_", " ").replace("-", " ").split())
        ok = (got_state == exp_state) and isinstance(got.get("state"), str)
        if ok:
            correct += 1
        # evidence check
        f1 = _ev_f1(got.get("evidence_ids", []), exp.get("evidence_ids", []))
        f1s.append(f1)
        per[key] = {"ok": ok, "got": got.get("state"), "expected": exp.get("state"),
                    "evidence_f1": f1}
        # Extra keys / wrong types break contract.
        if set(got.keys()) != {"entity", "state", "evidence_ids"}:
            broken = True
    if len(rows) != n:
        broken = True
    sem = (correct / n) if n else 0.0
    mean_f1 = (sum(f1s) / len(f1s)) if f1s else 0.0
    details = {"n_entities": n, "n_correct": correct, "n_got": len(rows),
               "per_entity": per, "evidence_f1_mean": mean_f1,
               "fenced": bool(info.get("fenced")), "prose": bool(info.get("prose")),
               "strict_json": bool(info.get("strict"))}
    if broken:
        return Verdict(status="FORMAT_ERROR", sub_reason="CONTRACT_BROKEN", sem=sem, strict=0.0,
                       details=details, attribution="MODEL")
    if sem < 1.0:
        # Partial credit: WRONG_ANSWER unless perfect.
        return Verdict(status="WRONG_ANSWER", sub_reason="BAD_STATES", sem=sem, strict=0.0,
                       details=details, attribution="MODEL")
    return Verdict(status="OK", sub_reason=None, sem=1.0, strict=1.0,
                   details=details, attribution="MODEL")
