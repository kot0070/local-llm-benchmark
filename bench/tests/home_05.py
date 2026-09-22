"""HOME-05 chart reading (home model gemma3:12b). Vision, R0, chat."""
from __future__ import annotations

import base64
import json
import os
import unicodedata

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-05", version="n1", title="Chart reading", family="VISION", home="gemma3:12b",
            kind="vision", mode="R0", requires=["vision"],
            num_predict=200, think_extra=1024, num_ctx=12288, timeout_s=240, core_n=8, empty_ok=False)

try:
    from bench.validate.jsonx import extract_json as _extract_json
except Exception:
    _extract_json = None

try:
    from bench.validate.textmetrics import norm_text as _norm_text
except Exception:
    _norm_text = None


def _local_extract(text):
    import re
    info = {"strict": False, "lenient": False, "fenced": False, "prose": False}
    s = (text or "").strip()
    if not s:
        return None, info
    try:
        return json.loads(s), {"strict": True, "lenient": True, "fenced": False, "prose": False}
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", s, re.DOTALL | re.IGNORECASE)
    body = s
    if m:
        info["fenced"] = True
        body = m.group(1)
        try:
            return json.loads(body.strip()), {"strict": False, "lenient": True, "fenced": True, "prose": True}
        except Exception:
            pass
    dec = json.JSONDecoder()
    for i, ch in enumerate(body):
        if ch in "{[":
            try:
                v, _e = dec.raw_decode(body[i:])
                info["lenient"] = True
                info["prose"] = True
                return v, info
            except Exception:
                continue
    return None, info


def _extract(text):
    if _extract_json is not None:
        try:
            return _extract_json(text)
        except Exception:
            pass
    return _local_extract(text)


def _norm_label(s):
    s = unicodedata.normalize("NFKC", str(s))
    import re
    s = re.sub(r"\s+", " ", s).strip().casefold()
    return s


def _is_english_only(profile):
    try:
        langs = getattr(profile, "langs", None)
        if langs == ["en"]:
            return True
    except Exception:
        pass
    tag = getattr(profile, "tag", "") or ""
    return tag == "granite3.2-vision:2b"


def load_cases(fixtures_dir: str) -> list[Case]:
    out = []
    with open(os.path.join(fixtures_dir, "cases.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-05"), tier=d.get("tier", ""),
                            lang=d.get("lang", "en"), input=d.get("input", {}),
                            expected=d.get("expected", {}), meta=d.get("meta", {})))
    return out


def _b64(fixtures_dir, rel):
    with open(os.path.join(fixtures_dir, rel), "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def build_request(case: Case, profile: Profile) -> Request:
    fixtures_dir = getattr(profile, "_fixtures_dir", None) or os.path.join("fixtures", "HOME-05")
    # runner resolves the asset; test keeps a relative reference too
    rel = case.input.get("image", "")
    images = []
    for cand in (os.path.join("fixtures", "HOME-05", rel), os.path.join(fixtures_dir, rel)):
        if os.path.isfile(cand):
            with open(cand, "rb") as f:
                images = [base64.b64encode(f.read()).decode("ascii")]
            break
    return Request(endpoint="chat",
                   messages=[{"role": "user", "content": case.input.get("question", ""), "images": images}])


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    if _is_english_only(profile) and (case.lang or "en") != "en":
        return Verdict(status="UNSUPPORTED_CAPABILITY", sub_reason="LANGUAGE_NOT_DOCUMENTED",
                       sem=0.0, strict=0.0,
                       details={"lang": case.lang, "expected": case.expected}, attribution="POLICY")
    content = resp.content or ""
    exp = case.expected or {}
    exp_ans = exp.get("answer")
    kind = exp.get("kind", "numeric" if isinstance(exp_ans, (int, float)) else "label")
    tol = float(exp.get("tol_rel", 0.005 if kind == "numeric" else 0.0))
    val, info = _extract(content)
    strict_json = bool(info.get("strict")) and isinstance(val, dict) and ("answer" in val)
    parsed = val.get("answer") if isinstance(val, dict) and "answer" in val else None
    if parsed is None and isinstance(val, (int, float, str)):
        parsed = val
    contract_ok = strict_json
    if kind == "numeric":
        try:
            got = float(str(parsed).replace(",", "").strip()) if not isinstance(parsed, bool) else None
        except Exception:
            got = None
        try:
            want = float(exp_ans)
        except Exception:
            want = None
        if got is None or want is None:
            sem = 0.0
        elif tol == 0.0:
            sem = 1.0 if got == want else 0.0
        else:
            sem = 1.0 if abs(got - want) <= tol * max(1.0, abs(want)) else 0.0
    else:
        sem = 1.0 if (parsed is not None and _norm_label(parsed) == _norm_label(exp_ans)) else 0.0
    details = {"parsed_answer": parsed, "expected": exp_ans, "kind": kind,
               "extract": info, "channel": "none", "sub_reason": None}
    if sem >= 1.0 and contract_ok:
        return Verdict(status="OK", sem=1.0, strict=1.0, details=details, attribution="MODEL")
    if sem >= 1.0 and not contract_ok:
        details["sub_reason"] = "CONTRACT_BROKEN"
        return Verdict(status="FORMAT_ERROR", sem=1.0, strict=0.0, details=details, attribution="MODEL")
    if not contract_ok and parsed is not None:
        details["sub_reason"] = "CONTRACT_BROKEN"
        return Verdict(status="FORMAT_ERROR", sem=float(sem), strict=0.0, details=details, attribution="MODEL")
    if not contract_ok:
        details["sub_reason"] = "UNPARSEABLE"
        return Verdict(status="FORMAT_ERROR", sem=0.0, strict=0.0, details=details, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sem=float(sem), strict=0.0, details=details, attribution="MODEL")
