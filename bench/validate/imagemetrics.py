"""Image/grounding metrics for BENCH V5 NIGHT-1 vision tests (owner: TASK_D).

Implements exactly (SPEC_NIGHT.md):
  iou(a, b)
  parse_boxes(text) -> list[{"label", "bbox": [x1, y1, x2, y2]}]

Plus local fallbacks (used when bench/validate/textmetrics.py is missing):
  levenshtein, cer, norm_ws, extract_json_value, parse_html_table,
  parse_markdown_table, grid_f1, dedupe_first_table.
Stdlib only.
"""
from __future__ import annotations

import json
import re
import unicodedata


# ---------------------------------------------------------------- iou

def _clip_box(b):
    x1, y1, x2, y2 = float(b[0]), float(b[1]), float(b[2]), float(b[3])
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    return (x1, y1, x2, y2)


def iou(a, b):
    """Intersection over union of two boxes [x1, y1, x2, y2]. Float in [0, 1]."""
    try:
        ax1, ay1, ax2, ay2 = _clip_box(a)
        bx1, by1, bx2, by2 = _clip_box(b)
    except Exception:
        return 0.0
    iw = min(ax2, bx2) - max(ax1, bx1)
    ih = min(ay2, by2) - max(ay1, by1)
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    aa = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    ab = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = aa + ab - inter
    if union <= 0:
        return 0.0
    v = inter / union
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


# ---------------------------------------------------------------- lenient JSON

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _strip_fences(text):
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1), True
    return text, False


def extract_json_value(text):
    """Lenient first-JSON-value extraction.

    Returns (value_or_None, info dict with strict/lenient/fenced/prose bools).
    strict = whole stripped text is one JSON value.
    """
    info = {"strict": False, "lenient": False, "fenced": False, "prose": False}
    if text is None:
        return None, info
    s = text.strip()
    if not s:
        return None, info
    try:
        v = json.loads(s)
        info["strict"] = True
        info["lenient"] = True
        return v, info
    except Exception:
        pass
    body, fenced = _strip_fences(s)
    info["fenced"] = fenced
    if fenced:
        try:
            v = json.loads(body.strip())
            info["lenient"] = True
            info["prose"] = (s.strip() != body.strip() and len(s) > len(body) + 6)
            return v, info
        except Exception:
            pass
    # scan for first JSON object/array
    starts = [i for i, ch in enumerate(body) if ch in "{["]
    for i in starts:
        sub = body[i:]
        # try incremental end candidates via raw decode
        dec = json.JSONDecoder()
        try:
            v, end = dec.raw_decode(sub)
            info["lenient"] = True
            info["prose"] = True
            return v, info
        except Exception:
            continue
    return None, info


def _coerce_num(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        t = x.strip().replace(",", "")
        try:
            if "." in t or "e" in t.lower():
                return float(t)
            return int(t)
        except Exception:
            return None
    return None


def parse_boxes(text):
    """Parse grounding boxes from model text.

    Accepts a JSON array (or single object) of {"label": str,
    "bbox_2d" (or "bbox"/"box"/"coordinates"): [x1,y1,x2,y2]}.
    Returns a list of {"label": str, "bbox": [f,f,f,f]}; invalid entries skipped.
    """
    val, _info = extract_json_value(text if isinstance(text, str) else "")
    if val is None:
        return []
    if isinstance(val, dict):
        val = [val]
    if not isinstance(val, list):
        return []
    out = []
    for item in val:
        if not isinstance(item, dict):
            continue
        label = item.get("label", item.get("name", item.get("text", "")))
        if not isinstance(label, str):
            label = str(label) if label is not None else ""
        box = None
        for key in ("bbox_2d", "bbox", "box", "coordinates", "coords", "xyxy"):
            if key in item and isinstance(item[key], (list, tuple)):
                box = item[key]
                break
        if box is None or len(box) != 4:
            continue
        nums = [_coerce_num(v) for v in box]
        if any(v is None for v in nums):
            continue
        out.append({"label": label, "bbox": [float(v) for v in nums]})
    return out


# ---------------------------------------------------------------- text fallbacks (OCR)

def norm_ws(s):
    """NFKC + collapse whitespace + strip (case preserved, for CER)."""
    if not isinstance(s, str):
        s = str(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def levenshtein(a, b):
    """Edit distance (code points)."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        ca = a[i - 1]
        for j in range(1, lb + 1):
            cost = 0 if ca == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[lb]


def cer(ref, hyp):
    """Char error rate after norm_ws. 0.0 for two empty strings."""
    r = norm_ws(ref)
    h = norm_ws(hyp)
    if not r and not h:
        return 0.0
    if not r:
        return 1.0
    return levenshtein(r, h) / max(1, len(r))


# ---------------------------------------------------------------- tables

def dedupe_first_table(text):
    """Keep only the first <table>...</table> block if present (GLM-OCR dedupe)."""
    if not isinstance(text, str):
        return text
    low = text.lower()
    s = low.find("<table")
    if s < 0:
        return text
    e = low.find("</table>", s)
    if e < 0:
        return text
    return text[s:e + len("</table>")]


def _clean_cell(s):
    if not isinstance(s, str):
        s = str(s)
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", " ", s.replace("\u00a0", " ")).strip()
    return s.casefold()


def parse_html_table(text):
    """Parse first HTML table into grid rows. Returns list[list[str]] or []."""
    if not isinstance(text, str):
        return []
    block = dedupe_first_table(text)
    rows = []
    for rm in re.finditer(r"<tr[^>]*>(.*?)</tr>", block, re.DOTALL | re.IGNORECASE):
        cells = []
        for cm in re.finditer(r"<t[dh][^>]*>(.*?)</t[dh]>", rm.group(1), re.DOTALL | re.IGNORECASE):
            cell = re.sub(r"<[^>]+>", "", cm.group(1))
            cell = cell.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            cells.append(cell.strip())
        if cells:
            rows.append(cells)
    return rows


def parse_markdown_table(text):
    """Parse a GitHub-style Markdown table into grid rows. Returns [] if none."""
    if not isinstance(text, str):
        return []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return []
    rows = []
    for ln in lines:
        parts = [p.strip() for p in ln.strip().strip("|").split("|")]
        rows.append(parts)
    # drop separator row (---|---)
    if len(rows) >= 2 and all(re.fullmatch(r":?-{1,}:?", c or "") for c in rows[1]):
        del rows[1]
    return rows


def parse_table_grid(text):
    """Parse HTML first, else Markdown. Returns grid rows."""
    g = parse_html_table(text)
    if g:
        return g
    return parse_markdown_table(text)


def grid_f1(got, expected):
    """Cell-level F1 over (row, col) after cleaning. Returns (f1, detail)."""
    exp = [[_clean_cell(c) for c in r] for r in expected]
    g = [[_clean_cell(c) for c in r] for r in got]
    n_exp = sum(len(r) for r in exp)
    n_got = sum(len(r) for r in g)
    n_rows = max(len(exp), len(g))
    n_cols = max(max((len(r) for r in exp), default=0), max((len(r) for r in g), default=0))
    tp = 0
    for i in range(n_rows):
        for j in range(n_cols):
            e = exp[i][j] if i < len(exp) and j < len(exp[i]) else None
            v = g[i][j] if i < len(g) and j < len(g[i]) else None
            if e is not None and v is not None and e == v:
                tp += 1
    prec = tp / n_got if n_got else (1.0 if n_exp == 0 else 0.0)
    rec = tp / n_exp if n_exp else (1.0 if n_got == 0 else 0.0)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return f1, {"tp": tp, "n_got": n_got, "n_exp": n_exp, "prec": prec, "rec": rec}
