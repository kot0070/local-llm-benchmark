"""HOME-12 NuExtract test (owner: TASK_B2). Raw adapter per SPEC; others chat+JSON."""
from __future__ import annotations

import json
import re

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-12", version="n1", title="Template extraction from long texts",
            family="EXTRACT", home="nuextract:3.8b", kind="chat", mode="R0",
            requires=["text"], num_predict=768, think_extra=1536,
            num_ctx=4096, timeout_s=180, core_n=8, empty_ok=False)


def _uses_raw(profile: Profile) -> bool:
    ad = getattr(profile, "adapters", {}) or {}
    return bool(ad.get("nuextract_raw")) if isinstance(ad, dict) else False


def _fallback_extract(text):
    s = text.strip()
    # strip end-output marker if present
    s = s.split("<|end-output|>")[0].strip()
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


try:
    from bench.validate.jsonx import extract_json as _ej
except ImportError:
    _ej = _fallback_extract


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def _leaf_eq(g, e) -> bool:
    if (g is None or g == "") and (e is None or e == ""):
        return True
    if isinstance(g, (int, float)) and isinstance(e, (int, float)):
        try:
            return abs(float(g) - float(e)) < 1e-9
        except Exception:
            return False
    # numeric string vs number
    if isinstance(g, (int, float)) or isinstance(e, (int, float)):
        try:
            return abs(float(g) - float(e)) < 1e-9
        except Exception:
            return False
    return str(g) == str(e)


def _field_f1(got: dict, exp: dict) -> tuple[float, dict, float, float]:
    gf, ef = flatten(got), flatten(exp)
    keys = set(gf) | set(ef)
    if not keys:
        return 1.0, {}, 1.0, 1.0
    correct = sum(1 for k in keys if k in gf and k in ef and _leaf_eq(gf[k], ef[k]))
    p = correct / len(gf) if gf else (1.0 if not ef else 0.0)
    r = correct / len(ef) if ef else (1.0 if not gf else 0.0)
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    per = {k: (1.0 if (k in gf and k in ef and _leaf_eq(gf[k], ef[k])) else 0.0) for k in sorted(keys)}
    return f1, per, p, r


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
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-12"),
                              tier=d.get("tier", ""), lang=d.get("lang", "en"),
                              input=d.get("input", {}), expected=d.get("expected"),
                              meta=d.get("meta", {})))
    return cases


def build_request(case: Case, profile: Profile) -> Request:
    tmpl = case.input.get("template", {})
    ex = case.input.get("example", {})
    text = case.input.get("text", "")
    if _uses_raw(profile):
        prompt = ("<|input|>\n### Template:\n" + json.dumps(tmpl, indent=4) +
                  "\n### Example:\n" + json.dumps(ex, indent=4) +
                  "\n### Text:\n" + text + "\n<|output|>\n")
        stops = list(getattr(profile, "stop", []) or []) + ["<|end-output|>"]
        return Request(endpoint="generate", prompt=prompt, raw=True,
                       options={"stop": stops})
    user = ("Extract the fields defined by the template from the text below. "
            "Output ONLY JSON matching the template; use \"\" for absent values. No prose, no code fences.\n\n"
            "Template:\n" + json.dumps(tmpl, indent=2) +
            "\n\nExample:\n" + json.dumps(ex, indent=2) +
            "\n\nText:\n" + text)
    return Request(endpoint="chat",
                   messages=[{"role": "user", "content": user}],
                   options={})


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    text = (resp.content or "").split("<|end-output|>")[0]
    exp = case.expected or {}
    src = case.input.get("text", "")
    obj, info = _ej(text)
    contract_ok = bool(info.get("strict")) and isinstance(obj, dict)
    if obj is None or not isinstance(obj, dict):
        return Verdict(status="FORMAT_ERROR", sub_reason="unparseable", sem=0.0, strict=0.0,
                       details={"parsed": None, "expected": exp, "info": info,
                                "precision": 0.0, "recall": 0.0, "hallucinated_fields": [],
                                "channel": "none"}, attribution="MODEL")
    f1, per, p, r = _field_f1(obj, exp)
    gf = flatten(obj)
    hallu = []
    for k, v in gf.items():
        if v is None or v == "":
            continue
        if isinstance(v, (int, float)):
            continue
        if str(v) not in src:
            hallu.append(k)
    details = {"parsed": obj, "expected": exp, "info": info, "per_field": per,
               "precision": p, "recall": r, "hallucinated_fields": sorted(hallu),
               "channel": "none"}
    if not contract_ok:
        reason = "code_fence" if info.get("fenced") else "prose_around_json"
        return Verdict(status="FORMAT_ERROR", sub_reason=reason, sem=f1, strict=0.0,
                       details=details, attribution="MODEL")
    if f1 >= 1.0 - 1e-9:
        return Verdict(status="OK", sub_reason="exact_match", sem=f1, strict=f1,
                       details=details, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sub_reason="field_mismatch", sem=f1, strict=f1,
                   details=details, attribution="MODEL")
