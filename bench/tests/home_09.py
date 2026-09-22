"""HOME-09 long-context wiki QA (owner: TASK_C)."""
from __future__ import annotations

import json
import os

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-09", version="n1", title="Long-context wiki QA", family="LONG",
            home="llama3.1:8b", kind="chat", mode="R0", requires=["text"],
            num_predict=512, think_extra=2048, num_ctx=20480, timeout_s=1500,
            core_n=4, empty_ok=False)

CONTRACT = ('Respond with ONLY a JSON object like {"answer": "<short answer>", "evidence": ["<section id>", "<section id>"]} '
            '(section ids are quoted strings) and nothing else.')


def load_cases(fixtures_dir: str) -> list[Case]:
    path = os.path.join(fixtures_dir, "cases.jsonl")
    cases: list[Case] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-09"), tier=d.get("tier", ""),
                              lang=d.get("lang", "en"), input=d.get("input", {}),
                              expected=d.get("expected", {}), meta=d.get("meta", {})))
    return cases


def build_request(case: Case, profile: Profile) -> Request:
    doc = case.input.get("document", "")
    q = case.input.get("question", "")
    content = (f"{doc}\n\nQuestion: {q}\n\n{CONTRACT} "
               "The answer must be a short exact string found in the document. "
               "Evidence must list the section ids (e.g. S001) that support the answer.")
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


def _evidence_f1(got_list, exp_list) -> tuple[float, dict]:
    def norm_ids(xs):
        out = set()
        for x in (xs or []):
            if isinstance(x, str):
                out.add(x.strip().upper())
        return out
    g = norm_ids(got_list)
    e = norm_ids(exp_list)
    if not g and not e:
        return 1.0, {"prec": 1.0, "rec": 1.0, "f1": 1.0}
    if not g or not e:
        return 0.0, {"prec": 0.0, "rec": 0.0, "f1": 0.0}
    tp = len(g & e)
    prec = tp / len(g)
    rec = tp / len(e)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return f1, {"prec": prec, "rec": rec, "f1": f1, "tp": tp,
                "n_got": len(g), "n_exp": len(e)}


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    from bench.validate.jsonx import extract_json
    text = resp.content or ""
    exp = case.expected or {}
    exp_answer = str(exp.get("answer", ""))
    exp_ev = exp.get("evidence", [])
    obj, info = extract_json(text)
    contract_broken = bool(info.get("fenced") or info.get("prose"))
    parsed = obj if isinstance(obj, dict) else None
    got_answer = ""
    got_ev: list = []
    if parsed is not None:
        a = parsed.get("answer", "")
        got_answer = a if isinstance(a, str) else (str(a) if a is not None else "")
        got_ev = parsed.get("evidence", [])
        if not isinstance(got_ev, list):
            got_ev = []
        # Contract requires exactly answer+evidence keys (allow only those).
        if set(parsed.keys()) != {"answer", "evidence"}:
            contract_broken = True
        if not isinstance(a, str):
            contract_broken = True
    else:
        contract_broken = True
    sem = 1.0 if (got_answer and _norm(got_answer) == _norm(exp_answer)) else 0.0
    # Lenient fallback: if dict parse failed, try answer substring match.
    if parsed is None and text.strip():
        if _norm(exp_answer) and _norm(exp_answer) in _norm(text):
            # Still counts semantically but contract is broken.
            sem = 1.0
    f1, f1d = _evidence_f1(got_ev, exp_ev)
    details = {"parsed_answer": got_answer, "expected": exp_answer,
               "evidence_f1": f1, "evidence_detail": f1d,
               "got_evidence": got_ev, "expected_evidence": exp_ev,
               "fenced": bool(info.get("fenced")), "prose": bool(info.get("prose")),
               "strict_json": bool(info.get("strict"))}
    if parsed is None:
        return Verdict(status="FORMAT_ERROR", sub_reason="NO_JSON", sem=sem, strict=0.0,
                       details=details, attribution="MODEL")
    if contract_broken:
        return Verdict(status="FORMAT_ERROR", sub_reason="CONTRACT_BROKEN", sem=sem, strict=0.0,
                       details=details, attribution="MODEL")
    if sem < 1.0:
        return Verdict(status="WRONG_ANSWER", sub_reason="BAD_ANSWER", sem=sem, strict=0.0,
                       details=details, attribution="MODEL")
    return Verdict(status="OK", sub_reason=None, sem=1.0, strict=1.0,
                   details=details, attribution="MODEL")
