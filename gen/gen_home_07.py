"""Generator for HOME-07 (document understanding, granite3.2-vision:2b). 8 docs x 2 Q = 16."""
from __future__ import annotations

import hashlib
import json
import os
import random

from PIL import Image, ImageDraw, ImageFont

TEST_ID = "HOME-07"
SEED = 707
IMG = 896
OUT = os.path.join("fixtures", TEST_ID)
FONTS_USED = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\consola.ttf"]
CONTRACT = 'Respond with JSON only: {"answer": "<value>"}. Use "NOT_PRESENT" if the requested information is not in the document.'

COMPANIES = ["Acme Traders Ltd", "Baltic Foods UAB", "Carpathian Steel", "Dnipro Logistics",
             "Emerald Textiles", "Fjord Metals AS", "Granite Works", "Harbor Freight Co"]
CITIES = ["Kyiv", "Riga", "Oslo", "Gdansk", "Tallinn", "Vilnius", "Lviv", "Bergen"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def font(size, bold=False):
    return ImageFont.truetype(FONTS_USED[1] if bold else FONTS_USED[0], size)


def render_doc(doc):
    im = Image.new("RGB", (IMG, IMG), (250, 250, 248))
    d = ImageDraw.Draw(im)
    d.rectangle([20, 20, IMG - 20, IMG - 20], outline=(0, 0, 0), width=3)
    d.text((50, 40), doc["company"], font=font(32, True), fill=(0, 0, 0))
    d.text((50, 84), f"INVOICE {doc['inv_id']}   Date: {doc['date']}   {doc['city']}", font=font(22), fill=(0, 0, 0))
    d.text((50, 116), f"Client: {doc['client']}   VAT: {doc['vat']}   Contact: {doc['phone']}", font=font(22), fill=(0, 0, 0))
    # table with merged header
    x0, y0 = 50, 170
    cols = [300, 160, 160, 140]
    d.rectangle([x0, y0, x0 + sum(cols), y0 + 36], fill=(30, 60, 120))
    d.text((x0 + 8, y0 + 4), "Statement of goods and services (all prices in EUR)", font=font(20, True), fill=(255, 255, 255))
    headers = ["Item", "Qty", "Unit price", "Total"]
    y = y0 + 36
    x = x0
    for h, w in zip(headers, cols):
        d.rectangle([x, y, x + w, y + 34], outline=(0, 0, 0), width=2, fill=(220, 228, 240))
        d.text((x + 8, y + 4), h, font=font(20, True), fill=(0, 0, 0))
        x += w
    y += 34
    mono = ImageFont.truetype(FONTS_USED[2], 20)
    for row in doc["rows"]:
        x = x0
        for txt, w in zip(row, cols):
            d.rectangle([x, y, x + w, y + 32], outline=(0, 0, 0), width=2)
            d.text((x + 8, y + 4), str(txt)[:22], font=mono, fill=(0, 0, 0))
            x += w
        y += 32
    # key-value block
    y += 12
    for k, v in doc["kv"].items():
        d.text((50, y), f"{k}: {v}", font=font(22), fill=(0, 0, 0))
        y += 30
    # small bar chart (quarterly revenue)
    cy = y + 10
    d.text((50, cy), "Quarterly revenue (kEUR):", font=font(22, True), fill=(0, 0, 0))
    cy += 32
    pal = [(31, 119, 180), (255, 127, 14), (44, 160, 44), (214, 39, 40)]
    mx = max(doc["quarters"])
    for i, v in enumerate(doc["quarters"]):
        bx = 60 + i * 190
        bh = int(v / mx * 120)
        d.rectangle([bx, cy + 130 - bh, bx + 90, cy + 130], fill=pal[i % 4], outline=(0, 0, 0), width=2)
        d.text((bx + 8, cy + 134), f"Q{i + 1}: {v}", font=font(20), fill=(0, 0, 0))
    d.text((50, cy + 168), f"Total due: EUR {doc['total']}", font=font(24, True), fill=(0, 0, 0))
    return im


def main():
    rng = random.Random(SEED)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    items = ["Steel beams", "Copper wire", "Oak planks", "Glass panels", "Bolts M12", "Paint drums"]
    cases = []
    for di in range(8):
        rows = []
        for r in range(4):
            item = items[(di + r) % len(items)]
            qty = rng.randint(2, 60)
            unit = rng.randint(5, 400)
            rows.append([item, str(qty), str(unit), str(qty * unit)])
        total = sum(int(r[3]) for r in rows)
        doc = {"company": COMPANIES[di], "city": CITIES[di], "inv_id": f"INV-2026-{1000 + di * 37}",
               "date": f"2026-0{(di % 9) + 1}-{(di * 3 % 27) + 1:02d}", "client": f"Client-{chr(65 + di)} Omega",
               "vat": f"VAT-{44000 + di * 111}", "phone": f"+380-67-100-20-0{di}",
               "rows": rows, "total": str(total),
               "kv": {"Payment terms": "30 days", "Delivery": f"Warehouse {di + 1}", "Manager": f"M. Shevchenko-{di}"},
               "quarters": [rng.randint(40, 300) for _ in range(4)]}
        asset = f"doc_{di:02d}.png"
        render_doc(doc).save(os.path.join(OUT, "assets", asset), format="PNG")
        # Q1: cell lookup (row i, Total column)
        ri = di % 4
        q1 = f"What is the Total (EUR) for '{doc['rows'][ri][0]}' in the table?"
        a1 = doc["rows"][ri][3]
        # Q2: alternate chart value / cross-ref / NOT_PRESENT
        if di % 4 == 0:
            q2 = "What is the revenue of Q3 (kEUR) shown in the quarterly chart?"
            a2 = str(doc["quarters"][2])
        elif di % 4 == 1:
            q2 = "What are the payment terms stated in the document?"
            a2 = doc["kv"]["Payment terms"]
        elif di % 4 == 2:
            q2 = "What discount rate is stated in the document?"
            a2 = "NOT_PRESENT"
        else:
            q2 = f"What is the invoice ID?"
            a2 = doc["inv_id"]
        q2b_kind = "notpresent" if a2 == "NOT_PRESENT" else ("numeric" if a2.isdigit() else "text")
        for qi, (q, a) in enumerate([(q1, a1), (q2, a2)]):
            tier = ["easy", "medium", "hard"][ (di + qi) % 3]
            kind = "numeric" if (qi == 0 or a.isdigit()) and a != "NOT_PRESENT" else ("notpresent" if a == "NOT_PRESENT" else "text")
            cases.append({"id": f"HOME-07-{len(cases) + 1:02d}", "test_id": TEST_ID, "tier": tier, "lang": "en",
                          "input": {"image": f"assets/{asset}", "question": q + " " + CONTRACT, "doc": di},
                          "expected": {"answer": a, "kind": kind},
                          "meta": {"doc": doc, "row_idx": ri, "qi": qi}})
    # stratify interleave
    by = {"easy": [], "medium": [], "hard": []}
    for c in cases:
        by[c["tier"]].append(c)
    ordered, ids = [], set()
    for k in range(max(len(v) for v in by.values())):
        for t in ("easy", "medium", "hard"):
            if k < len(by[t]):
                ordered.append(by[t][k])
    for i, c in enumerate(ordered):
        c["id"] = f"HOME-07-{i + 1:02d}"
    # verify: recompute answers from meta
    for c in ordered:
        m = c["meta"]
        doc = m["doc"]
        exp = doc["rows"][m["row_idx"]][3] if m["qi"] == 0 else c["expected"]["answer"]
        assert exp == c["expected"]["answer"], c["id"]
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
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_07.py",
                "fonts": {os.path.basename(p): sha256_file(p) for p in FONTS_USED},
                "files": files, "n_cases": len(ordered)}
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, sort_keys=True, indent=2)
    man = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    for rel, h in man["files"].items():
        assert sha256_file(os.path.join(OUT, rel)) == h, rel
    print(f"HOME-07: {len(ordered)} cases ok")


if __name__ == "__main__":
    main()
