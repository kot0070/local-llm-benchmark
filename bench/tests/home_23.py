"""HOME-23 OCR (home model glm-ocr:latest). Vision, R0, chat."""
from __future__ import annotations

import base64
import json
import os

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-23", version="n1", title="OCR transcription", family="OCR",
            home="glm-ocr:latest", kind="vision", mode="R0", requires=["vision"],
            num_predict=1024, think_extra=0, num_ctx=12288, timeout_s=180, core_n=10, empty_ok=False)

try:
    from bench.validate.imagemetrics import cer as _cer, grid_f1 as _grid_f1, parse_table_grid as _parse_grid, dedupe_first_table as _dedupe
except Exception:
    _cer = _grid_f1 = _parse_grid = _dedupe = None

import re
import unicodedata


def _norm_ws(s):
    s = unicodedata.normalize("NFKC", str(s)).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).strip()


def _lev(a, b):
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if not la:
        return lb
    if not lb:
        return la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if a[i - 1] == b[j - 1] else 1))
        prev = cur
    return prev[lb]


def _local_cer(ref, hyp):
    r, h = _norm_ws(ref), _norm_ws(hyp)
    if not r and not h:
        return 0.0
    if not r:
        return 1.0
    return _lev(r, h) / max(1, len(r))


def _clean_cell(s):
    return _norm_ws(s).casefold()


def _local_grid_f1(got, expected):
    exp = [[_clean_cell(c) for c in r] for r in expected]
    g = [[_clean_cell(c) for c in r] for r in got]
    n_exp = sum(len(r) for r in exp)
    n_got = sum(len(r) for r in g)
    n = max(len(exp), len(g))
    m = max(max((len(r) for r in exp), default=0), max((len(r) for r in g), default=0))
    tp = 0
    for i in range(n):
        for j in range(m):
            e = exp[i][j] if i < len(exp) and j < len(exp[i]) else None
            v = g[i][j] if i < len(g) and j < len(g[i]) else None
            if e is not None and v == e:
                tp += 1
    prec = tp / n_got if n_got else (1.0 if n_exp == 0 else 0.0)
    rec = tp / n_exp if n_exp else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return f1, {"tp": tp, "n_got": n_got, "n_exp": n_exp, "prec": prec, "rec": rec}


def _local_parse_grid(text):
    t = text or ""
    low = t.lower()
    s = low.find("<table")
    if s >= 0:
        e = low.find("</table>", s)
        block = t[s:e + 8] if e >= 0 else t[s:]
        rows = []
        for rm in re.finditer(r"<tr[^>]*>(.*?)</tr>", block, re.DOTALL | re.IGNORECASE):
            cells = [re.sub(r"<[^>]+>", "", cm.group(1)).strip()
                     for cm in re.finditer(r"<t[dh][^>]*>(.*?)</t[dh]>", rm.group(1), re.DOTALL | re.IGNORECASE)]
            if cells:
                rows.append(cells)
        if rows:
            return rows
    lines = [ln.strip() for ln in t.splitlines() if ln.strip().startswith("|")]
    if len(lines) >= 2:
        rows = [[p.strip() for p in ln.strip().strip("|").split("|")] for ln in lines]
        if len(rows) >= 2 and all(re.fullmatch(r":?-{1,}:?", c or "") for c in rows[1]):
            del rows[1]
        return rows
    return []


def _is_glmocr(profile):
    try:
        return bool((getattr(profile, "adapters", None) or {}).get("glmocr_prompts"))
    except Exception:
        return False


def load_cases(fixtures_dir: str) -> list[Case]:
    out = []
    with open(os.path.join(fixtures_dir, "cases.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-23"), tier=d.get("tier", ""),
                            lang=d.get("lang", "en"), input=d.get("input", {}),
                            expected=d.get("expected", {}), meta=d.get("meta", {})))
    return out


def build_request(case: Case, profile: Profile) -> Request:
    rel = case.input.get("image", "")
    images = []
    for cand in (os.path.join("fixtures", "HOME-23", rel), rel):
        if os.path.isfile(cand):
            with open(cand, "rb") as f:
                images = [base64.b64encode(f.read()).decode("ascii")]
            break
    mode = case.input.get("mode", "text")
    opts = {}
    if _is_glmocr(profile):
        text = "Table Recognition:" if mode == "table" else "Text Recognition:"
        if mode == "text":
            opts = {"stop": ["\n```"]}
    else:
        text = ("Convert the table to an HTML <table>. Output only the table." if mode == "table"
                else "Transcribe all text in the image exactly. Output only the text.")
    return Request(endpoint="chat", messages=[{"role": "user", "content": text, "images": images}],
                   options=opts)


_FENCE_LINE_RE = re.compile(r"^\s*```[\w-]*\s*$")


def _collapse_consecutive_seq(seq, key):
    if not seq:
        return [], 0
    out = [seq[0]]
    removed = 0
    for item in seq[1:]:
        try:
            dup = key(item) == key(out[-1])
        except Exception:
            dup = item == out[-1]
        if dup:
            removed += 1
        else:
            out.append(item)
    return out, removed


def _collapse_repeated_block(seq, key):
    n = len(seq)
    if n < 2:
        return seq, 0
    try:
        keys = [key(x) for x in seq]
    except Exception:
        keys = list(seq)
    for k in range(1, n // 2 + 1):
        if n % k != 0:
            continue
        pat = keys[:k]
        if all(keys[i] == pat[i % k] for i in range(n)):
            return list(seq[:k]), n - k
    return seq, 0


def _dedup_text_content(content):
    """Drop fence-only lines and collapse consecutive duplicate blocks.

    Returns (cleaned, blocks_removed, fences_removed).
    """
    lines = (content or "").splitlines()
    fences_removed = sum(1 for ln in lines if _FENCE_LINE_RE.match(ln))
    kept = [ln for ln in lines if not _FENCE_LINE_RE.match(ln)]
    stripped = "\n".join(kept).strip()
    if not stripped:
        return "", 0, fences_removed
    paras = re.split(r"\n\s*\n", stripped)
    paras, r1 = _collapse_consecutive_seq(paras, _norm_ws)
    paras, r1b = _collapse_repeated_block(paras, _norm_ws)
    stage = "\n\n".join(paras)
    lns = stage.splitlines()
    lns, r2 = _collapse_consecutive_seq(lns, _norm_ws)
    lns, r2b = _collapse_repeated_block(lns, _norm_ws)
    cleaned = "\n".join(lns).strip()
    blocks_removed = r1 + r1b + r2 + r2b
    return cleaned, blocks_removed, fences_removed


def _row_key(row):
    return tuple(_clean_cell(c) for c in row)


def _collapse_grid_rows(rows):
    if not rows:
        return rows, 0
    out, r1 = _collapse_consecutive_seq(list(rows), _row_key)
    out, r2 = _collapse_repeated_block(out, _row_key)
    return out, r1 + r2


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    content = resp.content or ""
    mode = case.input.get("mode", case.meta.get("mode", "text"))
    cer_fn = _cer or _local_cer
    grid_fn = _grid_f1 or _local_grid_f1
    parse_fn = _parse_grid or _local_parse_grid
    if mode == "table":
        exp_rows = case.expected.get("rows", [])
        dedup = (_dedupe(content) if _dedupe else None) or content
        # dedupe helper keeps first table; local parser already prefers first table
        got = parse_fn(dedup if _dedupe else content)
        collapsed, rows_removed = _collapse_grid_rows(got)
        if rows_removed:
            f1, det = grid_fn(collapsed, exp_rows)
            sem = float(f1)
            details = {"f1": f1, "cell_detail": det, "parsed_grid": collapsed,
                       "expected_grid": exp_rows, "mode": "table", "channel": "none",
                       "sub_reason": "REPETITION_LOOP",
                       "dedup_removed_blocks": int(rows_removed)}
            return Verdict(status="FORMAT_ERROR", sem=float(sem), strict=0.0,
                           details=details, attribution="MODEL")
        f1, det = grid_fn(collapsed, exp_rows)
        sem = float(f1)
        details = {"f1": f1, "cell_detail": det, "parsed_grid": collapsed, "expected_grid": exp_rows,
                   "mode": "table", "channel": "none", "sub_reason": None}
        contract_ok = bool(collapsed)
        if sem >= 1.0 and contract_ok:
            return Verdict(status="OK", sem=1.0, strict=1.0, details=details, attribution="MODEL")
        if not contract_ok:
            details["sub_reason"] = "UNPARSEABLE_TABLE"
            return Verdict(status="FORMAT_ERROR", sem=0.0, strict=0.0, details=details, attribution="MODEL")
        return Verdict(status="WRONG_ANSWER", sem=float(sem), strict=0.0, details=details, attribution="MODEL")
    want = case.expected.get("text", "")
    cleaned, blocks_removed, fences_removed = _dedup_text_content(content)
    if blocks_removed or fences_removed:
        n_removed = int(blocks_removed if blocks_removed else fences_removed)
        cer = cer_fn(want, cleaned)
        sem = max(0.0, 1.0 - float(cer))
        details = {"cer": float(cer), "hyp": cleaned[:500], "expected": want,
                   "mode": "text", "channel": "none", "sub_reason": "REPETITION_LOOP",
                   "dedup_removed_blocks": n_removed}
        return Verdict(status="FORMAT_ERROR", sem=float(sem), strict=0.0,
                       details=details, attribution="MODEL")
    cer = cer_fn(want, content)
    sem = max(0.0, 1.0 - float(cer))
    details = {"cer": float(cer), "hyp": content[:500], "expected": want,
               "mode": "text", "channel": "none", "sub_reason": None}
    # plain-text contract: fences / prose wrappers break it
    t = content.strip()
    contract_ok = not (t.startswith("```") or t.lower().startswith("transcription"))
    if sem >= 0.95 and contract_ok:
        return Verdict(status="OK", sem=float(sem), strict=float(sem), details=details, attribution="MODEL")
    if sem >= 0.95 and not contract_ok:
        details["sub_reason"] = "CONTRACT_BROKEN"
        return Verdict(status="FORMAT_ERROR", sem=float(sem), strict=0.0, details=details, attribution="MODEL")
    if not content.strip():
        details["sub_reason"] = "EMPTY"
        return Verdict(status="FORMAT_ERROR", sem=0.0, strict=0.0, details=details, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sem=float(sem), strict=0.0, details=details, attribution="MODEL")
