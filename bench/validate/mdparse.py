"""Markdown parser for HOME-19 (owner: TASK_B2). Stdlib only."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

_FENCE_RE = re.compile(r"^```(\w*)\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_TABLE_SEP_RE = re.compile(r"^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$")


def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.casefold()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def unwrap_code_fence(text: str) -> tuple[str, bool]:
    """If the whole answer is wrapped in one ``` fence, unwrap it.

    Returns (unwrapped, was_wrapped).
    """
    s = text.strip()
    if s.startswith("```") and s.endswith("```"):
        lines = s.splitlines()
        if len(lines) >= 2 and lines[0].lstrip().startswith("```"):
            inner = "\n".join(lines[1:-1])
            # handle single-line ```md ... ``` case
            if len(lines) == 2:
                m = re.match(r"^```\w*\s*(.*)```\s*$", s, re.DOTALL)
                if m:
                    inner = m.group(1)
            return inner.strip(), True
    return text, False


def _split_table_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def parse_markdown(text: str) -> dict:
    """Parse Markdown into blocks.

    Returns dict with keys: headings, paragraphs, list_items, table_cells,
    tables, code_blocks, links, images.
    - headings: [{"level": int, "text": str}]
    - paragraphs: [str]
    - list_items: [{"depth": int, "ordered": bool, "text": str}]
    - table_cells: [{"table": int, "row": int, "col": int, "header": bool, "text": str}]
    - tables: [{"header": [str], "rows": [[str]]}]
    - code_blocks: [str]
    - links: [{"href": str, "text": str}]
    - images: [{"href": str, "text": str}]
    """
    headings: list[dict] = []
    paragraphs: list[str] = []
    list_items: list[dict] = []
    table_cells: list[dict] = []
    tables: list[dict] = []
    code_blocks: list[str] = []
    links: list[dict] = []
    images: list[dict] = []

    lines = text.splitlines()
    in_code = False
    code_lang = ""
    code_buf: list[str] = []
    para_buf: list[str] = []
    indent_stack: list[int] = []  # list nesting; reset by any non-list block
    i = 0

    def flush_para():
        if para_buf:
            # join continuation lines with space
            p = " ".join(s.strip() for s in para_buf if s.strip()).strip()
            if p:
                paragraphs.append(p)
            para_buf.clear()

    def collect_links(s: str):
        for m in _LINK_RE.finditer(s):
            bang, ltext, href = m.group(1), m.group(2), m.group(3)
            if bang == "!":
                images.append({"href": href, "text": ltext})
            else:
                links.append({"href": href, "text": ltext})

    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        # code fence handling
        if stripped.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = stripped[3:].strip()
                code_buf = []
            else:
                in_code = False
                code_blocks.append("\n".join(code_buf))
                code_buf = []
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        # heading
        mh = _HEADING_RE.match(stripped)
        if mh:
            flush_para()
            indent_stack.clear()
            level = len(mh.group(1))
            htext = mh.group(2).strip()
            headings.append({"level": level, "text": htext})
            collect_links(htext)
            i += 1
            continue
        # setext heading (CommonMark): paragraph text underlined with === (h1) or --- (h2)
        if (stripped and i + 1 < n and "|" not in line
                and re.match(r"^ {0,3}(=+|-+)\s*$", lines[i + 1])
                and not re.match(r"^(\s*)([-*+]|\d+[.)])\s+", line)):
            htext = " ".join(s.strip() for s in para_buf + [line] if s.strip()).strip()
            para_buf.clear()
            indent_stack.clear()
            level = 1 if lines[i + 1].strip().startswith("=") else 2
            headings.append({"level": level, "text": htext})
            collect_links(htext)
            i += 2
            continue
        # table detection: header row + separator row
        if "|" in line and i + 1 < n and _TABLE_SEP_RE.match(lines[i + 1]):
            flush_para()
            indent_stack.clear()
            header = _split_table_row(line)
            # skip separator
            i += 2
            rows: list[list[str]] = []
            while i < n and "|" in lines[i] and lines[i].strip() != "" and not _TABLE_SEP_RE.match(lines[i]):
                rows.append(_split_table_row(lines[i]))
                i += 1
            t_idx = len(tables)
            tables.append({"header": header, "rows": rows})
            for c, h in enumerate(header):
                table_cells.append({"table": t_idx, "row": -1, "col": c, "header": True, "text": h})
                collect_links(h)
            for r, row in enumerate(rows):
                for c, cell in enumerate(row):
                    table_cells.append({"table": t_idx, "row": r, "col": c, "header": False, "text": cell})
                    collect_links(cell)
            for h in header:
                pass
            continue
        # list item
        m_list = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if m_list:
            flush_para()
            indent = m_list.group(1).replace("\t", "    ")
            # depth = nesting level from an indent stack, not raw spaces // 2
            # ("1.  item" nests children at 4 spaces, "- item" at 2; both are depth 1)
            ind = len(indent)
            while indent_stack and ind < indent_stack[-1]:
                indent_stack.pop()
            if not indent_stack or ind > indent_stack[-1]:
                indent_stack.append(ind)
            depth = len(indent_stack) - 1
            marker = m_list.group(2)
            ordered = bool(re.match(r"^\d+[.)]$", marker))
            ltext = m_list.group(3).strip()
            list_items.append({"depth": depth, "ordered": ordered, "text": ltext})
            collect_links(ltext)
            i += 1
            continue
        # horizontal rule / empty
        if stripped == "" or re.match(r"^(\*\*\*+|---+|___+)$", stripped):
            flush_para()
            i += 1
            continue
        # html-ish boilerplate lines starting with < (nav etc.) - treat as paragraph text
        if not line[:1].isspace():  # top-level paragraph ends any list
            indent_stack.clear()
        para_buf.append(line)
        collect_links(line)
        i += 1
    flush_para()
    if in_code:
        code_blocks.append("\n".join(code_buf))

    return {
        "headings": headings,
        "paragraphs": paragraphs,
        "list_items": list_items,
        "table_cells": table_cells,
        "tables": tables,
        "code_blocks": code_blocks,
        "links": links,
        "images": images,
    }


def _multiset_f1(gold: list, pred: list) -> float:
    if not gold and not pred:
        return 1.0
    if not gold or not pred:
        return 0.0
    cg = Counter(gold)
    cp = Counter(pred)
    inter = sum((cg & cp).values())
    if inter == 0:
        return 0.0
    p = inter / sum(cp.values())
    r = inter / sum(cg.values())
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def block_scores(gold: dict, pred: dict) -> tuple[float, dict]:
    """Macro F1 over block types present in gold.

    Types: headings, list_items, table_cells, code_blocks, links.
    Returns (macro_f1, per_type dict).
    """
    per: dict[str, float] = {}
    g_h = [(h["level"], norm_text(h["text"])) for h in gold.get("headings", [])]
    p_h = [(h["level"], norm_text(h["text"])) for h in pred.get("headings", [])]
    g_li = [(li["depth"], norm_text(li["text"])) for li in gold.get("list_items", [])]
    p_li = [(li["depth"], norm_text(li["text"])) for li in pred.get("list_items", [])]
    g_tc = [(c["table"], c["row"], c["col"], norm_text(c["text"])) for c in gold.get("table_cells", [])]
    p_tc = [(c["table"], c["row"], c["col"], norm_text(c["text"])) for c in pred.get("table_cells", [])]
    g_cb = [norm_text(c) for c in gold.get("code_blocks", [])]
    p_cb = [norm_text(c) for c in pred.get("code_blocks", [])]
    g_lk = [(norm_text(l["href"]), norm_text(l["text"])) for l in gold.get("links", [])]
    p_lk = [(norm_text(l["href"]), norm_text(l["text"])) for l in pred.get("links", [])]

    candidates = {
        "headings": (g_h, p_h),
        "list_items": (g_li, p_li),
        "table_cells": (g_tc, p_tc),
        "code_blocks": (g_cb, p_cb),
        "links": (g_lk, p_lk),
    }
    vals = []
    for k, (g, p) in candidates.items():
        if len(g) > 0:
            f = _multiset_f1(g, p)
            per[k] = f
            vals.append(f)
    macro = sum(vals) / len(vals) if vals else 1.0
    return macro, per


def text_token_f1(ref: str, hyp: str) -> float:
    rt = norm_text(ref).split()
    ht = norm_text(hyp).split()
    if not rt and not ht:
        return 1.0
    if not rt or not ht:
        return 0.0
    return _multiset_f1(rt, ht)
