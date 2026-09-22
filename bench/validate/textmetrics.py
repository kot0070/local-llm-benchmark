"""Shared text metrics for BENCH V5 NIGHT-1 (owner: TASK_B1). Stdlib only."""
from __future__ import annotations

import unicodedata


def norm_text(s: str) -> str:
    """NFKC, casefold, collapse whitespace."""
    if s is None:
        return ""
    t = unicodedata.normalize("NFKC", str(s)).casefold()
    return " ".join(t.split())


def levenshtein(a, b) -> int:
    """Edit distance on sequences (strings or lists)."""
    if isinstance(a, str):
        a = list(a)
    else:
        a = list(a)
    if isinstance(b, str):
        b = list(b)
    else:
        b = list(b)
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    if m > n:
        a, b = b, a
        n, m = m, n
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        ai = a[i - 1]
        for j in range(1, m + 1):
            cost = 0 if ai == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[m]


def cer(ref: str, hyp: str) -> float:
    """Character error rate (raw strings). 0 for two empties, 1 if ref empty."""
    ref = "" if ref is None else str(ref)
    hyp = "" if hyp is None else str(hyp)
    if not ref:
        return 0.0 if not hyp else 1.0
    return levenshtein(ref, hyp) / len(ref)


def wer(ref: str, hyp: str) -> float:
    """Word error rate (whitespace tokenisation)."""
    ref_w = str("" if ref is None else ref).split()
    hyp_w = str("" if hyp is None else hyp).split()
    if not ref_w:
        return 0.0 if not hyp_w else 1.0
    return levenshtein(ref_w, hyp_w) / len(ref_w)


def token_f1(ref: str, hyp: str) -> float:
    """Multiset token F1 over norm_text tokens."""
    r = norm_text(ref).split()
    h = norm_text(hyp).split()
    if not r and not h:
        return 1.0
    if not r or not h:
        return 0.0
    from collections import Counter

    cr, ch = Counter(r), Counter(h)
    overlap = sum((cr & ch).values())
    if overlap == 0:
        return 0.0
    p = overlap / sum(ch.values())
    rec = overlap / sum(cr.values())
    return 2 * p * rec / (p + rec)
