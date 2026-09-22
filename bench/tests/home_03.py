"""HOME-03 RAG test (owner: TASK_B2)."""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-03", version="n1", title="RAG with citations and abstention",
            family="RAG", home="command-r7b:7b", kind="chat", mode="R0",
            requires=["text"], num_predict=300, think_extra=2048,
            num_ctx=8192, timeout_s=180, core_n=10, empty_ok=False)

SYSTEM = ("You answer questions using ONLY the provided documents. Return ONLY a JSON object with keys: "
          '"answer" (string with the exact answer, or null if the documents do not contain the answer), '
          '"citations" (array of document ids like ["D1"] that support the answer), '
          '"abstain" (true if unanswerable, else false). No prose, no code fences.')


def _fallback_extract(text):
    s = text.strip()
    fenced = "```" in text
    try:
        return json.loads(s), {"strict": True, "lenient": True, "fenced": fenced, "prose": False}
    except Exception:
        pass
    cleaned = re.sub(r"```\w*\n?", " ", text).replace("```", " ")
    dec = json.JSONDecoder()
    for m in re.finditer(r"[\{\[]", cleaned):
        try:
            obj, _ = dec.raw_decode(cleaned[m.start():])
            return obj, {"strict": False, "lenient": True, "fenced": fenced, "prose": True}
        except Exception:
            continue
    return None, {"strict": False, "lenient": False, "fenced": fenced, "prose": True}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.casefold()
    return re.sub(r"\s+", " ", s).strip()


try:
    from bench.validate.jsonx import extract_json as _ej
except ImportError:
    _ej = _fallback_extract
try:
    from bench.validate.textmetrics import norm_text as _norm_tm, token_f1 as _tf1
    _HAS_TM = True
except ImportError:
    _HAS_TM = False
    _norm_tm = _norm

    def _tf1(ref: str, hyp: str) -> float:
        rt, ht = _norm(ref).split(), _norm(hyp).split()
        if not rt and not ht:
            return 1.0
        if not rt or not ht:
            return 0.0
        cr, ch = Counter(rt), Counter(ht)
        inter = sum((cr & ch).values())
        if inter == 0:
            return 0.0
        return 2 * inter / (sum(cr.values()) + sum(ch.values()))


def _norm_fact(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s))
    s = s.casefold()
    s = s.replace("-", " ").replace("_", " ").replace("/", " ")
    s = s.replace("$", " usd ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\byears\b", "year", s)
    s = re.sub(r"\bdays\b", "day", s)
    s = re.sub(r"\bhours\b", "hour", s)
    s = re.sub(r"\bdollars?\b", "usd", s)
    return re.sub(r"\s+", " ", s).strip()


def _extract_numbers(s: str) -> list[float]:
    out = []
    for m in re.finditer(r"\d+(?:\.\d+)?", str(s)):
        try:
            out.append(float(m.group(0)))
        except Exception:
            pass
    return out


def _fact_present(fact: str, answer: str) -> bool:
    nf = _norm_fact(fact)
    na = _norm_fact(answer)
    if not nf:
        return True
    if nf in na:
        return True
    # numeric-aware fallback: same number + remaining tokens present
    try:
        m = re.search(r"\d+(?:\.\d+)?", str(fact))
        if m:
            fv = float(m.group(0))
            for av in _extract_numbers(answer):
                if abs(av - fv) < 1e-9:
                    rest = re.sub(r"\d+(?:\.\d+)?", " ", nf).strip()
                    toks = [t for t in re.split(r"\s+", rest) if t]
                    if not toks or all(t in na for t in toks):
                        return True
    except Exception:
        pass
    return False


def _facts_score(got_ans, facts: list) -> tuple[float, dict]:
    if not facts:
        return 1.0, {}
    if got_ans is None:
        return 0.0, {f: 0.0 for f in facts}
    per = {}
    for f in facts:
        per[str(f)] = 1.0 if _fact_present(str(f), str(got_ans)) else 0.0
    sem = 1.0 if all(v >= 1.0 for v in per.values()) else 0.0
    return sem, per


def _answer_correct(got, exp, facts=None) -> float:
    if exp is None:
        return 1.0 if got is None else 0.0
    if got is None:
        return 0.0
    if facts:
        sem, _ = _facts_score(got, facts)
        return sem
    gs, es = str(got).strip(), str(exp).strip()
    if _norm(gs) == _norm(es):
        return 1.0
    try:
        if abs(float(gs.replace(",", "")) - float(es.replace(",", ""))) < 1e-9:
            return 1.0
    except Exception:
        pass
    # numeric substring tolerance for synthesis answers: token F1 >= 0.9 counts
    if _tf1(es, gs) >= 0.9:
        return 1.0
    return 0.0


def _cite_scores(got_cites, exp_cites) -> tuple[float, float, float]:
    g = set(str(x) for x in (got_cites or []))
    e = set(str(x) for x in (exp_cites or []))
    if not g and not e:
        return 1.0, 1.0, 1.0
    if not g or not e:
        return 0.0, 0.0, 0.0
    inter = len(g & e)
    p = inter / len(g)
    r = inter / len(e)
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def load_cases(fixtures_dir: str) -> list[Case]:
    import os
    path = os.path.join(fixtures_dir, "cases.jsonl")
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-03"),
                              tier=d.get("tier", ""), lang=d.get("lang", "en"),
                              input=d.get("input", {}), expected=d.get("expected"),
                              meta=d.get("meta", {})))
    return cases


def build_request(case: Case, profile: Profile) -> Request:
    docs = case.input.get("documents", [])
    parts = []
    for d in docs:
        parts.append(f"[{d['id']}] {d.get('title', '')} (effective {d.get('effective_date', '')}):\n{d.get('text', '')}")
    user = ("Documents:\n\n" + "\n\n".join(parts) + "\n\nQuestion: " + case.input.get("question", ""))
    return Request(endpoint="chat",
                   messages=[{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": user}],
                   options={})


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    text = resp.content or ""
    exp = case.expected or {}
    obj, info = _ej(text)
    contract_ok = bool(info.get("strict")) and isinstance(obj, dict)
    if obj is None or not isinstance(obj, dict):
        return Verdict(status="FORMAT_ERROR", sub_reason="unparseable", sem=0.0, strict=0.0,
                       details={"parsed": None, "expected": exp, "info": info,
                                "citation_precision": 0.0, "citation_recall": 0.0, "citation_f1": 0.0},
                       attribution="MODEL")
    exp_ans = exp.get("answer")
    exp_cites = exp.get("citations", [])
    exp_abs = bool(exp.get("abstain"))
    exp_facts = exp.get("facts", [])
    got_ans = obj.get("answer")
    got_cites = obj.get("citations", [])
    got_abs = bool(obj.get("abstain", False))
    if exp_ans is None:
        sem = 1.0 if (got_ans is None and got_abs) else 0.0
        fact_detail: dict = {}
    else:
        sem = _answer_correct(got_ans, exp_ans, exp_facts if exp_facts else None)
        _, fact_detail = _facts_score(got_ans, exp_facts if exp_facts else [])
        if got_abs:
            sem = 0.0
    p, r, f = _cite_scores(got_cites if isinstance(got_cites, list) else [], exp_cites)
    details = {"parsed": obj, "expected": exp, "info": info,
               "answer_correct": sem, "fact_scores": fact_detail,
               "citation_precision": p, "citation_recall": r, "citation_f1": f,
               "channel": "none"}
    if not contract_ok:
        reason = "code_fence" if info.get("fenced") else "prose_around_json"
        return Verdict(status="FORMAT_ERROR", sub_reason=reason, sem=sem, strict=0.0,
                       details=details, attribution="MODEL")
    if sem >= 1.0 - 1e-9:
        return Verdict(status="OK", sub_reason="answer_match", sem=sem, strict=sem,
                       details=details, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sub_reason="answer_mismatch", sem=sem, strict=sem,
                   details=details, attribution="MODEL")
