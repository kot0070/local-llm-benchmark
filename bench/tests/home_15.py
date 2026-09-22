"""HOME-15 visual grounding (home model qwen2.5vl:7b). Vision, R0, chat."""
from __future__ import annotations

import base64
import json
import os

from bench.types import Case, Profile, Request, Response, Verdict

META = dict(id="HOME-15", version="n1", title="Visual grounding", family="VISION_GROUND",
            home="qwen2.5vl:7b", kind="vision", mode="R0", requires=["vision"],
            num_predict=256, think_extra=1024, num_ctx=12288, timeout_s=180, core_n=12, empty_ok=False)

IMG = 896

try:
    from bench.validate.imagemetrics import iou as _iou, parse_boxes as _parse_boxes, extract_json_value as _exj
except Exception:
    _iou = _parse_boxes = _exj = None


def _local_iou(a, b):
    ax1, ay1, ax2, ay2 = (float(a[0]), float(a[1]), float(a[2]), float(a[3]))
    bx1, by1, bx2, by2 = (float(b[0]), float(b[1]), float(b[2]), float(b[3]))
    if ax1 > ax2:
        ax1, ax2 = ax2, ax1
    if ay1 > ay2:
        ay1, ay2 = ay2, ay1
    if bx1 > bx2:
        bx1, bx2 = bx2, bx1
    if by1 > by2:
        by1, by2 = by2, by1
    iw = min(ax2, bx2) - max(ax1, bx1)
    ih = min(ay2, by2) - max(ay1, by1)
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union > 0 else 0.0


def _local_parse(text):
    try:
        v = json.loads((text or "").strip())
    except Exception:
        import re
        m = re.search(r"```(?:json)?\s*(.*?)\s*```", text or "", re.DOTALL | re.IGNORECASE)
        body = m.group(1) if m else (text or "")
        dec = json.JSONDecoder()
        v = None
        for i, ch in enumerate(body):
            if ch in "{[":
                try:
                    v, _e = dec.raw_decode(body[i:])
                    break
                except Exception:
                    continue
        if v is None:
            return [], {"strict": False, "lenient": False, "fenced": bool(m), "prose": True}
    strict = False
    try:
        strict = json.loads((text or "").strip()) is not None and (text or "").strip().startswith("[")
    except Exception:
        strict = False
    items = v if isinstance(v, list) else ([v] if isinstance(v, dict) else [])
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        box = None
        for k in ("bbox_2d", "bbox", "box", "coordinates"):
            if isinstance(it.get(k), (list, tuple)) and len(it[k]) == 4:
                box = it[k]
                break
        if box is None:
            continue
        try:
            out.append({"label": str(it.get("label", "")), "bbox": [float(x) for x in box]})
        except Exception:
            continue
    return out, {"strict": strict, "lenient": bool(out), "fenced": "```" in (text or ""), "prose": not strict}


def _convention(profile):
    try:
        return ((getattr(profile, "adapters", None) or {}).get("grounding_coords") or "").strip()
    except Exception:
        return ""


def load_cases(fixtures_dir: str) -> list[Case]:
    out = []
    with open(os.path.join(fixtures_dir, "cases.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-15"), tier=d.get("tier", ""),
                            lang=d.get("lang", "en"), input=d.get("input", {}),
                            expected=d.get("expected", {}), meta=d.get("meta", {})))
    return out


def build_request(case: Case, profile: Profile) -> Request:
    rel = case.input.get("image", "")
    images = []
    for cand in (os.path.join("fixtures", "HOME-15", rel), rel):
        if os.path.isfile(cand):
            with open(cand, "rb") as f:
                images = [base64.b64encode(f.read()).decode("ascii")]
            break
    gc = _convention(profile)
    desc = case.input.get("description", "the target")
    size = case.input.get("image_size", IMG)
    if gc == "absolute_px":
        instr = (f"Locate {desc} in the image. Respond with JSON only: "
                 f'[{{"label": "<label>", "bbox_2d": [x1, y1, x2, y2]}}] '
                 f"with ABSOLUTE PIXEL coordinates of the {size}x{size} image.")
    elif gc == "rel_1000":
        instr = (f"Locate {desc} in the image. Respond with JSON only: "
                 f'[{{"label": "<label>", "bbox_2d": [x1, y1, x2, y2]}}] '
                 f"with coordinates on the 0-1000 scale (x=1000 is the right edge, y=1000 the bottom edge).")
    else:
        instr = (f"Locate {desc} in the image. Respond with JSON only: "
                 f'[{{"label": "<label>", "bbox_2d": [x1, y1, x2, y2]}}] '
                 f"with pixel coordinates of the {size}x{size} image (origin top-left).")
    return Request(endpoint="chat", messages=[{"role": "user", "content": instr, "images": images}])


def _to_pixels(box, requested):
    if requested == "rel_1000":
        return [v / 1000.0 * IMG for v in box]
    # default/absolute_px: assume pixels, but tolerate 0-1000 if clearly relative
    if requested in ("", "absolute_px", None):
        if max(abs(v) for v in box) <= 1000 and max(abs(v) for v in box) <= 1000:
            # ambiguous: keep as pixels (documented contract); only rescale when the
            # request explicitly asked for rel_1000
            pass
        return list(box)
    return list(box)


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    content = resp.content or ""
    exp = case.expected or {}
    want_box = [float(v) for v in exp.get("bbox", [0, 0, 0, 0])]
    want_label = str(exp.get("label", ""))
    requested = _convention(profile)
    if _parse_boxes is not None and _iou is not None and _exj is not None:
        boxes = _parse_boxes(content)
        val, info = _exj(content)
        strict_json = bool(info.get("strict")) and isinstance(val, (list, dict))
        iou_fn = _iou
    else:
        boxes, info = _local_parse(content)
        strict_json = bool(info.get("strict"))
        iou_fn = _local_iou
    contract_ok = strict_json and len(boxes) >= 1
    best, best_label = 0.0, ""
    for b in boxes:
        px = _to_pixels(b["bbox"], requested)
        px = [min(max(v, 0.0), float(IMG)) for v in px]
        v = iou_fn(px, want_box)
        if v > best:
            best, best_label = v, b.get("label", "")
    # label bonus is informational only; score is pure IoU
    sem = 1.0 if best >= 0.5 else 0.0
    detected = "rel_1000" if requested == "rel_1000" else "absolute_px"
    details = {"iou": best, "expected_bbox": want_box, "expected_label": want_label,
               "got": boxes[:3], "best_label": best_label, "label_match": (best_label == want_label),
               "detected_convention": detected, "requested_convention": requested or "absolute_px(default)",
               "extract": info, "channel": "none", "sub_reason": None}
    if sem >= 1.0 and contract_ok:
        return Verdict(status="OK", sem=1.0, strict=1.0, details=details, attribution="MODEL")
    if sem >= 1.0 and not contract_ok:
        details["sub_reason"] = "CONTRACT_BROKEN"
        return Verdict(status="FORMAT_ERROR", sem=1.0, strict=0.0, details=details, attribution="MODEL")
    if not contract_ok and boxes:
        details["sub_reason"] = "CONTRACT_BROKEN"
        return Verdict(status="FORMAT_ERROR", sem=float(sem), strict=0.0, details=details, attribution="MODEL")
    if not contract_ok and not boxes:
        details["sub_reason"] = "UNPARSEABLE"
        return Verdict(status="FORMAT_ERROR", sem=0.0, strict=0.0, details=details, attribution="MODEL")
    return Verdict(status="WRONG_ANSWER", sem=float(sem), strict=0.0, details=details, attribution="MODEL")
