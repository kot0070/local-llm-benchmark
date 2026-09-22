"""HOME-02 cross-lingual retrieval (owner: TASK_C)."""
from __future__ import annotations

import json
import math
import os

from bench.types import Case, Profile, Response, Verdict

META = dict(id="HOME-02", version="n1", title="Cross-lingual retrieval", family="EMBED",
            home="bge-m3:latest", kind="embed", mode="-", requires=["embed"],
            num_predict=0, think_extra=0, num_ctx=0, timeout_s=900,
            core_n=40, empty_ok=False)


def _find_corpus(fixtures_dir: str) -> str:
    cand = os.path.join(fixtures_dir, "corpus.jsonl")
    if os.path.exists(cand):
        return cand
    parent = os.path.dirname(os.path.abspath(fixtures_dir))
    alt = os.path.join(parent, "HOME-02", "corpus.jsonl")
    return alt


def load_cases(fixtures_dir: str) -> list[Case]:
    path = os.path.join(fixtures_dir, "cases.jsonl")
    cases: list[Case] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            meta = d.get("meta", {}) or {}
            meta = dict(meta)
            meta["fixtures_dir"] = os.path.abspath(fixtures_dir)
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-02"), tier=d.get("tier", ""),
                              lang=d.get("lang", "en"), input=d.get("input", {}),
                              expected=d.get("expected", {}), meta=meta))
    return cases


def load_corpus(fixtures_dir: str) -> list[dict]:
    path = _find_corpus(fixtures_dir)
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _langs_supported(profile: Profile, query_lang: str, targets: list[str]) -> tuple[bool, str]:
    langs = getattr(profile, "langs", None)
    # profiles.json may not be loaded into Profile; check adapters? Fall back to allow.
    # The runner builds Profile from config; langs is not a dataclass field, so it may
    # live in profile.notes/adapters. We check attribute 'langs' if present else allow.
    if langs is None:
        langs = getattr(profile, "adapters", {}).get("langs", None)
    if langs is None:
        return True, ""
    low = {str(x).casefold() for x in langs}
    # "multi" means broad coverage.
    if "multi" in low:
        return True, ""
    q = str(query_lang or "").casefold()
    if q and q not in low:
        return False, f"query lang '{query_lang}' not in {sorted(low)}"
    for t in targets:
        if str(t).casefold() not in low:
            return False, f"target lang '{t}' not in {sorted(low)}"
    return True, ""


def run_embed(cases: list[Case], profile: Profile, embed_fn) -> list[tuple[Case, Verdict]]:
    from bench.validate.retrieval import ndcg_at_k, recall_at_k, rank_first_relevant, reciprocal_rank, cosine_sim
    # Resolve corpus dir from first case meta if available.
    fixtures_dir = None
    for c in cases:
        d = (c.meta or {}).get("fixtures_dir")
        if d:
            fixtures_dir = d
            break
    corpus: list[dict] = []
    if fixtures_dir and os.path.isdir(fixtures_dir):
        try:
            corpus = load_corpus(fixtures_dir)
        except Exception:
            corpus = []
    if not corpus:
        # Fallback: corpus embedded in case inputs (not expected, but safe).
        seen: dict = {}
        for c in cases:
            for p in (c.input.get("corpus") or []):
                if isinstance(p, dict) and p.get("id"):
                    seen[p["id"]] = p
        corpus = list(seen.values())
    doc_ids = [p["id"] for p in corpus]
    doc_texts = [str(p.get("text", "")) for p in corpus]
    doc_langs = {p["id"]: str(p.get("lang", "en")) for p in corpus}
    qprefix = ""
    dprefix = ""
    try:
        ep = getattr(profile, "embed_prefix", None) or {}
        qprefix = str(ep.get("query", "") or "")
        dprefix = str(ep.get("document", "") or "")
    except Exception:
        pass
    out: list[tuple[Case, Verdict]] = []
    if not corpus:
        for c in cases:
            out.append((c, Verdict(status="HARNESS_ERROR", sub_reason="NO_CORPUS", sem=0.0,
                                   strict=0.0, details={}, attribution="HARNESS")))
        return out
    # Embed corpus once.
    try:
        dresp = embed_fn([dprefix + t for t in doc_texts])
        demb = dresp.embeddings or []
    except Exception as e:
        for c in cases:
            out.append((c, Verdict(status="HARNESS_ERROR", sub_reason="EMBED_FAIL", sem=0.0,
                                   strict=0.0, details={"error": str(e)}, attribution="HARNESS")))
        return out
    if len(demb) != len(doc_ids):
        for c in cases:
            out.append((c, Verdict(status="HARNESS_ERROR", sub_reason="EMBED_COUNT", sem=0.0,
                                   strict=0.0, details={}, attribution="HARNESS")))
        return out
    for c in cases:
        q = str(c.input.get("query", ""))
        qlang = str(c.input.get("query_lang", c.lang or "en"))
        qrels = c.expected.get("qrels", {}) if isinstance(c.expected, dict) else {}
        targets = sorted({doc_langs.get(d, "en") for d in qrels.keys()})
        ok, reason = _langs_supported(profile, qlang, targets)
        if not ok:
            out.append((c, Verdict(status="UNSUPPORTED_CAPABILITY", sub_reason="LANGUAGE_NOT_DOCUMENTED",
                                   sem=0.0, strict=0.0, details={"reason": reason}, attribution="POLICY")))
            continue
        try:
            qresp = embed_fn([qprefix + q])
            qemb = (qresp.embeddings or [None])[0]
        except Exception as e:
            out.append((c, Verdict(status="HARNESS_ERROR", sub_reason="EMBED_FAIL", sem=0.0,
                                   strict=0.0, details={"error": str(e)}, attribution="HARNESS")))
            continue
        if qemb is None:
            out.append((c, Verdict(status="HARNESS_ERROR", sub_reason="EMBED_EMPTY", sem=0.0,
                                   strict=0.0, details={}, attribution="HARNESS")))
            continue
        scored = sorted(((cosine_sim(list(qemb), list(d)), did) for d, did in zip(demb, doc_ids)),
                        key=lambda x: -x[0])
        ranked = [did for _, did in scored]
        sem = ndcg_at_k(ranked, qrels, 10)
        rfr = rank_first_relevant(ranked, qrels)
        rr = reciprocal_rank(ranked, qrels)
        rec = recall_at_k(ranked, qrels, 10)
        details = {"ranked_top10": ranked[:10], "rank_first_relevant": rfr,
                   "reciprocal_rank": rr, "recall@10": rec, "nDCG@10": sem,
                   "qrels": qrels}
        out.append((c, Verdict(status="OK" if sem >= 1.0 else "WRONG_ANSWER",
                               sub_reason=None if sem >= 1.0 else "RANKING",
                               sem=float(sem), strict=float(sem),
                               details=details, attribution="MODEL")))
    return out
