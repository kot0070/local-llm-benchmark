"""Generator for HOME-15 (visual grounding, qwen2.5vl:7b). 12 scenes with exact bboxes."""
from __future__ import annotations

import hashlib
import json
import os
import random

from PIL import Image, ImageDraw, ImageFont

TEST_ID = "HOME-15"
SEED = 1515
IMG = 896
OUT = os.path.join("fixtures", TEST_ID)
FONTS_USED = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"]

SHAPES = ["red button", "blue circle", "green checkbox", "yellow banner", "purple input field", "teal icon"]
FILL = {"red button": (220, 60, 60), "blue circle": (60, 120, 220), "green checkbox": (60, 180, 90),
        "yellow banner": (235, 200, 60), "purple input field": (150, 100, 220), "teal icon": (40, 170, 170)}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def font(size, bold=False):
    return ImageFont.truetype(FONTS_USED[1] if bold else FONTS_USED[0], size)


def draw_object(d, kind, box, label):
    x1, y1, x2, y2 = box
    if kind == "blue circle":
        d.ellipse(box, fill=FILL[kind], outline=(0, 0, 0), width=3)
    elif kind == "green checkbox":
        d.rectangle(box, fill=(255, 255, 255), outline=(0, 0, 0), width=4)
        d.line([x1 + 8, (y1 + y2) / 2, (x1 + x2) / 2, y2 - 10], fill=(30, 150, 60), width=6)
        d.line([(x1 + x2) / 2, y2 - 10, x2 - 8, y1 + 10], fill=(30, 150, 60), width=6)
    else:
        d.rectangle(box, fill=FILL[kind], outline=(0, 0, 0), width=3)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    d.text((cx - 60, cy - 14), label[:14], font=font(24), fill=(0, 0, 0))


def main():
    rng = random.Random(SEED)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    cases = []
    for i in range(12):
        n = 3 + (i % 4)  # 3..6
        kinds = rng.sample(SHAPES, n)
        boxes, labels, taken = [], [], []
        for j, k in enumerate(kinds):
            for _try in range(60):
                w = rng.randint(120, 220)
                h = rng.randint(70, 130)
                x = rng.randint(40, IMG - 40 - w)
                y = rng.randint(90, IMG - 60 - h)
                box = [x, y, x + w, y + h]
                if all(x + w < bx or bx + bw < x or y + h < by or by + bh < y
                       for (bx, by, bw, bh) in taken):
                    taken.append((x, y, w, h))
                    boxes.append(box)
                    labels.append(f"{k.split()[0].upper()}-{i}{j}")
                    break
        ti = (i * 5) % n
        target_kind, target_box, target_label = kinds[ti], boxes[ti], labels[ti]
        desc = f"the {target_kind} labeled \"{target_label}\""
        asset = f"scene_{i:02d}.png"
        im = Image.new("RGB", (IMG, IMG), (242, 242, 240))
        d = ImageDraw.Draw(im)
        d.text((40, 28), f"Screen {i + 1}: click the requested widget", font=font(28, True), fill=(0, 0, 0))
        for k, b, lb in zip(kinds, boxes, labels):
            draw_object(d, k, b, lb)
        im.save(os.path.join(OUT, "assets", asset), format="PNG")
        tier = ["easy", "medium", "hard"][i % 3]
        cases.append({"id": f"HOME-15-{i + 1:02d}", "test_id": TEST_ID, "tier": tier, "lang": "en",
                      "input": {"image": f"assets/{asset}", "description": desc, "image_size": IMG},
                      "expected": {"label": target_label, "bbox": target_box},
                      "meta": {"objects": [{"label": lb, "kind": k, "bbox": b} for lb, k, b in zip(labels, kinds, boxes)],
                               "target": ti}})
    by = {"easy": [], "medium": [], "hard": []}
    for c in cases:
        by[c["tier"]].append(c)
    ordered = []
    for k in range(4):
        for t in ("easy", "medium", "hard"):
            if k < len(by[t]):
                ordered.append(by[t][k])
    for i, c in enumerate(ordered):
        c["id"] = f"HOME-15-{i + 1:02d}"
    # verify: expected bbox equals meta target; box inside image; area>0
    for c in ordered:
        m = c["meta"]
        tb = m["objects"][m["target"]]["bbox"]
        assert list(tb) == list(c["expected"]["bbox"]), c["id"]
        assert m["objects"][m["target"]]["label"] == c["expected"]["label"]
        x1, y1, x2, y2 = tb
        assert 0 <= x1 < x2 <= IMG and 0 <= y1 < y2 <= IMG
        ap = os.path.join(OUT, c["input"]["image"])
        assert os.path.isfile(ap) and os.path.getsize(ap) > 0
        with Image.open(ap) as im2:
            assert im2.size == (IMG, IMG)
    with open(os.path.join(OUT, "cases.jsonl"), "w", encoding="utf-8") as f:
        for c in ordered:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    files = {}
    for root, _ds, fns in os.walk(OUT):
        for fn in sorted(fns):
            if fn == "manifest.json":
                continue
            fp = os.path.join(root, fn)
            files[os.path.relpath(fp, OUT).replace(os.sep, "/")] = sha256_file(fp)
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_15.py",
                "fonts": {os.path.basename(p): sha256_file(p) for p in FONTS_USED},
                "files": files, "n_cases": len(ordered)}
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, sort_keys=True, indent=2)
    man = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    for rel, h in man["files"].items():
        assert sha256_file(os.path.join(OUT, rel)) == h, rel
    print(f"HOME-15: {len(ordered)} cases ok")


if __name__ == "__main__":
    main()
