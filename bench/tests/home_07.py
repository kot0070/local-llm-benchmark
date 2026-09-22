"""HOME-07 document understanding (home model granite3.2-vision:2b). Vision, R0, chat."""
from __future__ import annotations

import base64
import json
import os
import re
import unicodedata

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-07", version="n1", title="Document understanding", family="DOCVIS",
            home="granite3.2-vision:2b", kind="vision", mode="R0", requires=["vision"],
            num_predict=120, think_extra=1024, num_ctx=12288, timeout_s=180, core_n=10, empty_ok=False)

try:
    from bench.validate.jsonx import extract_json as _extract_json
except Exception:
    _extract_json = None


def _local_extract(text):
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


def _norm(s):
    s = unicodedata.normalize("NFKC", str(s))
    s = re.sub(r"\s+", " ", s.replace("\u00a0", " ")).strip().casefold()
    return s


def _num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except Exception:
        return None


def load_cases(fixtures_dir: str) -> list[Case]:
    out = []
    with open(os.path.join(fixtures_dir, "cases.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-07"), tier=d.get("tier", ""),
                            lang=d.get("lang", "en"), input=d.get("input", {}),
                            expected=d.get("expected", {}), meta=d.get("meta", {})))
    return out


def _adapters(profile) -> dict:
    try:
        if isinstance(profile, dict):
            return profile.get("adapters", {}) or {}
        return getattr(profile, "adapters", {}) or {}
    except Exception:
        return {}


def _plain_strip(s: str) -> str:
    t = (s or "").strip()
    # drop fenced block wrapper if present
    if t.startswith("```") and t.endswith("```") and len(t) >= 6:
        inner = t[3:-3].strip()
        # drop optional language tag on first line
        if "\n" in inner:
            first, rest = inner.split("\n", 1)
            if re.fullmatch(r"[A-Za-z0-9_+-]+", first.strip()):
                inner = rest.strip()
        t = inner
    # drop a leading "Answer:" label
    if t.lower().startswith("answer:"):
        t = t[len("answer:"):].strip()
    # drop surrounding quotes/backticks (possibly repeated)
    for _ in range(3):
        if len(t) >= 2 and t[0] == t[-1] and t[0] in ("'", '"', "`"):
            t = t[1:-1].strip()
            continue
        if len(t) >= 2 and t[0] in ("'", '"', "`", "\u201c", "\u201d", "\u2018", "\u2019") and t[-1] in ("'", '"', "`", "\u201c", "\u201d", "\u2018", "\u2019"):
            t = t[1:-1].strip()
            continue
        break
    # trailing "Answer:"-style label already handled; final strip
    return t.strip()


def _plain_num(s: str):
    try:
        m = re.search(r"-?\d[\d,]*\.?\d*", str(s))
        if not m:
            return None
        return float(m.group(0).replace(",", ""))
    except Exception:
        return None


def build_request(case: Case, profile: Profile) -> Request:
    rel = case.input.get("image", "")
    images = []
    for cand in (os.path.join("fixtures", "HOME-07", rel), rel):
        if os.path.isfile(cand):
            with open(cand, "rb") as f:
                images = [base64.b64encode(f.read()).decode("ascii")]
            break
    adapters = _adapters(profile)
    if adapters.get("plain_answer"):
        q = case.input.get("question", "")
        marker = "Respond with JSON only"
        assert marker in q, "plain_answer adapter requires the JSON sentence in the fixture question"
        base = q.split(marker)[0].strip()
        question = (base + " Answer with the value only, in a few words, no JSON."
                    " If the information is not in the document, answer NOT_PRESENT.")
        return Request(endpoint="chat",
                       messages=[{"role": "user", "content": question, "images": images}])
    return Request(endpoint="chat",
                   messages=[{"role": "user", "content": case.input.get("question", ""), "images": images}])


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    content = resp.content or ""
    exp = case.expected or {}
    want = exp.get("answer", "")
    kind = exp.get("kind", "text")
    adapters = _adapters(profile)
    if adapters.get("plain_answer"):
        details = {"parsed_answer": None, "expected": want, "kind": kind,
                   "channel": "plain", "sub_reason": None, "adapter": "plain_answer"}
        # Model falling back to tool-call syntax or a DocTags dump is still a contract break.
        if "<tool_call" in content or "<doc" in content:
            details["sub_reason"] = "UNPARSEABLE"
            return Verdict(status="FORMAT_ERROR", sem=0.0, strict=0.0, details=details, attribution="MODEL")
        parsed = _plain_strip(content)
        details["parsed_answer"] = parsed
        if not parsed:
            details["sub_reason"] = "UNPARSEABLE"
            return Verdict(status="FORMAT_ERROR", sem=0.0, strict=0.0, details=details, attribution="MODEL")
        if kind == "notpresent":
            sem = 1.0 if _norm(parsed) == "not_present" else 0.0
        elif kind == "numeric":
            g, w = _plain_num(parsed), _num(want)
            sem = 1.0 if (g is not None and w is not None and g == w) else 0.0
        else:
            sem = 1.0 if _norm(parsed) == _norm(want) else 0.0
        if sem >= 1.0:
            return Verdict(status="OK", sem=1.0, strict=1.0, details=details, attribution="MODEL")
        # Lenient fallback: accept a correct JSON {"answer": ...} even under the plain adapter,
        # so a model that keeps emitting JSON is still scored on value.
        try:
            val, _info = _extract(content)
            jparsed = val.get("answer") if isinstance(val, dict) and "answer" in val else None
            if jparsed is None and isinstance(val, str):
                jparsed = val
            if jparsed is not None:
                if kind == "notpresent":
                    jsem = 1.0 if _norm(jparsed) == "not_present" else 0.0
                elif kind == "numeric":
                    gj, wj = _num(jparsed), _num(want)
                    jsem = 1.0 if (gj is not None and wj is not None and gj == wj) else 0.0
                else:
                    jsem = 1.0 if _norm(jparsed) == _norm(want) else 0.0
                if jsem >= 1.0:
                    details["parsed_answer"] = jparsed
                    return Verdict(status="OK", sem=1.0, strict=1.0, details=details, attribution="MODEL")
        except Exception:
            pass
        return Verdict(status="WRONG_ANSWER", sem=float(sem), strict=0.0, details=details, attribution="MODEL")
    val, info = _extract(content)
    strict_json = bool(info.get("strict")) and isinstance(val, dict) and ("answer" in val)
    parsed = val.get("answer") if isinstance(val, dict) and "answer" in val else None
    if parsed is None and isinstance(val, str):
        parsed = val
    contract_ok = strict_json
    if kind == "notpresent":
        # canonical answer is the literal string "NOT_PRESENT"
        sem = 1.0 if (parsed is not None and _norm(parsed) == "not_present") else 0.0
    elif kind == "numeric":
        g, w = _num(parsed), _num(want)
        sem = 1.0 if (g is not None and w is not None and g == w) else 0.0
    else:
        sem = 1.0 if (parsed is not None and _norm(parsed) == _norm(want)) else 0.0
    details = {"parsed_answer": parsed, "expected": want, "kind": kind,
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
