"""HOME-19 HTML->Markdown test (owner: TASK_B2). Reader-LM raw HTML adapter."""
from __future__ import annotations

import json

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-19", version="n1", title="HTML to Markdown conversion",
            family="DOCTX", home="reader-lm:1.5b", kind="chat", mode="R0",
            requires=["text"], num_predict=3000, think_extra=1024,
            num_ctx=12288, timeout_s=600, core_n=4, empty_ok=False)

INSTRUCTION = ("Convert the main content of the following HTML to Markdown. "
               "Output only Markdown, no explanations, no code fences around the whole answer.")

try:
    from bench.validate.mdparse import (block_scores, parse_markdown, text_token_f1,
                                        unwrap_code_fence)
except ImportError:  # pragma: no cover
    raise


def _uses_raw(profile: Profile) -> bool:
    ad = getattr(profile, "adapters", {}) or {}
    return bool(ad.get("reader_raw_html")) if isinstance(ad, dict) else False


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
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-19"),
                              tier=d.get("tier", ""), lang=d.get("lang", "en"),
                              input=d.get("input", {}), expected=d.get("expected"),
                              meta=d.get("meta", {})))
    return cases


def build_request(case: Case, profile: Profile) -> Request:
    html = case.input.get("html", "")
    if _uses_raw(profile):
        return Request(endpoint="chat",
                       messages=[{"role": "user", "content": html}],
                       options={})
    return Request(endpoint="chat",
                   messages=[{"role": "user", "content": INSTRUCTION + "\n\n" + html}],
                   options={})


def _strip_boilerplate(text: str, boiler: list[str]) -> str:
    out = text
    for b in boiler or []:
        if b:
            out = out.replace(b, " ")
    return out


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    raw = resp.content or ""
    exp_md = (case.expected or {}).get("markdown", "")
    boiler = (case.meta or {}).get("boilerplate", [])
    unwrapped, was_wrapped = unwrap_code_fence(raw)
    # whole answer wrapped in ``` -> FORMAT_ERROR, sem computed after unwrapping
    contract_broken = was_wrapped or ("```" in unwrapped and unwrapped.strip().startswith("```"))
    pred_clean = _strip_boilerplate(unwrapped, boiler)
    gold_blocks = parse_markdown(exp_md)
    pred_blocks = parse_markdown(pred_clean)
    macro, per_type = block_scores(gold_blocks, pred_blocks)
    tok_f1 = text_token_f1(exp_md, pred_clean)
    sem = float(max(0.0, min(1.0, 0.5 * macro + 0.5 * tok_f1)))
    # boilerplate ratio: fraction of raw output matching boilerplate phrases
    b_hits = sum(len(b) for b in (boiler or []) if b and b in raw)
    b_ratio = min(1.0, b_hits / max(1, len(raw)))
    details = {"macro_block_f1": macro, "per_type_f1": per_type, "text_token_f1": tok_f1,
               "boilerplate_ratio": b_ratio, "wrapped_in_fence": was_wrapped,
               "channel": "none"}
    if contract_broken:
        return Verdict(status="FORMAT_ERROR", sub_reason="code_fence", sem=sem, strict=0.0,
                       details=details, attribution="MODEL")
    if sem >= 1.0 - 1e-9:
        return Verdict(status="OK", sub_reason="exact_match", sem=sem, strict=sem,
                       details=details, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sub_reason="content_mismatch", sem=sem, strict=sem,
                   details=details, attribution="MODEL")
