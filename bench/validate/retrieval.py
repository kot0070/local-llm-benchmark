"""Retrieval metrics for BENCH V5 NIGHT-1 embeddings tests (owner: TASK_C).

Graded qrels: {doc_id: gain} with gains 0/1/2.
Stdlib only.
"""
from __future__ import annotations

import math


def dcg_at_k(ranked_ids: list, qrels: dict, k: int = 10) -> float:
    s = 0.0
    for i, doc_id in enumerate(ranked_ids[:k]):
        rel = int(qrels.get(doc_id, 0) or 0)
        if rel > 0:
            s += (2.0 ** rel - 1.0) / math.log2(i + 2)
    return s


def ndcg_at_k(ranked_ids: list, qrels: dict, k: int = 10) -> float:
    """Graded nDCG@k. 0.0 when there is no relevant doc."""
    qrels = qrels or {}
    ideal = sorted((int(v or 0) for v in qrels.values()), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal):
        if rel > 0:
            idcg += (2.0 ** rel - 1.0) / math.log2(i + 2)
    if idcg <= 0:
        return 0.0
    return dcg_at_k(ranked_ids, qrels, k) / idcg


def recall_at_k(ranked_ids: list, qrels: dict, k: int = 10) -> float:
    """Fraction of relevant docs (gain > 0) retrieved in top-k."""
    qrels = qrels or {}
    rel_docs = {d for d, g in qrels.items() if int(g or 0) > 0}
    if not rel_docs:
        return 0.0
    hit = sum(1 for d in ranked_ids[:k] if d in rel_docs)
    return hit / len(rel_docs)


def reciprocal_rank(ranked_ids: list, qrels: dict) -> float:
    """1/rank of the first relevant doc (gain > 0); 0.0 if none."""
    qrels = qrels or {}
    for i, doc_id in enumerate(ranked_ids):
        if int(qrels.get(doc_id, 0) or 0) > 0:
            return 1.0 / (i + 1)
    return 0.0


def mrr(ranked_lists: list, qrels_list: list) -> float:
    """Mean reciprocal rank over multiple queries."""
    if not ranked_lists:
        return 0.0
    tot = 0.0
    for ranked, q in zip(ranked_lists, qrels_list):
        tot += reciprocal_rank(ranked, q or {})
    return tot / len(ranked_lists)


def rank_first_relevant(ranked_ids: list, qrels: dict) -> int | None:
    """1-based rank of the first relevant doc, or None."""
    qrels = qrels or {}
    for i, doc_id in enumerate(ranked_ids):
        if int(qrels.get(doc_id, 0) or 0) > 0:
            return i + 1
    return None


def cosine_sim(a: list, b: list) -> float:
    """Cosine similarity between two dense vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na * nb)
