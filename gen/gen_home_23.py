"""Generator for HOME-23 (OCR, glm-ocr:latest). 10 text crops + 6 tables."""
from __future__ import annotations

import hashlib
import json
import os
import random

from PIL import Image, ImageDraw, ImageFont, ImageFilter

TEST_ID = "HOME-23"
SEED = 2323
IMG = 896
OUT = os.path.join("fixtures", TEST_ID)
F_ARIAL = r"C:\Windows\Fonts\arial.ttf"
F_ARIALB = r"C:\Windows\Fonts\arialbd.ttf"
F_CONSOLA = r"C:\Windows\Fonts\consola.ttf"
F_ZH = r"C:\Windows\Fonts\msyh.ttc"
FONTS_USED = [F_ARIAL, F_ARIALB, F_CONSOLA, F_ZH]

TEXTS = [
    ("en", "The harbor warehouse received forty-two crates of copper wire on Tuesday morning. Delivery note #4821 was signed by the night guard."),
    ("en", "Quarterly maintenance is scheduled for the first weekend of October. All servers will be offline between 02:00 and 06:00."),
    ("uk", "Склад прийняв сорок дві палети з кабельною продукцією у вівторок зранку. Накладну №4821 підписав нічний охоронець."),
    ("uk", "Щоквартальне обслуговування заплановано на перші вихідні жовтня. Усі сервери будуть недоступні з 02:00 до 06:00."),
    ("de", "Das Lager hat am Dienstagmorgen zweiundvierzig Paletten mit Kabeln erhalten. Lieferschein Nr. 4821 wurde vom Nachtwächter unterschrieben."),
    ("de", "Die vierteljährliche Wartung findet am ersten Oktoberwochenende statt. Alle Server sind zwischen 02:00 und 06:00 Uhr offline."),
    ("es", "El almacén recibió cuarenta y dos palés de cable el martes por la mañana. El albarán n.º 4821 fue firmado por el vigilante nocturno."),
    ("en", "Invoice INV-2026-1042 totals EUR 1,240.50. Payment is due within thirty days of the issue date."),
    ("uk", "Рахунок №2026-1042 на суму 1240,50 євро. Оплата протягом тридцяти днів від дати виставлення."),
    ("zh", "港口仓库于周二上午收到了四十二箱铜线。夜间警卫签署了第4821号交货单。"),
]
TABLES = [
    {"headers": ["Item", "Qty", "Price"], "rows": [["Bolts M12", "40", "1.20"], ["Oak planks", "12", "34.50"], ["Paint drums", "7", "58.00"]]},
    {"headers": ["Name", "City", "Dept", "Ext"], "rows": [["I. Petrenko", "Kyiv", "Sales", "221"], ["O. Koval", "Lviv", "Support", "314"], ["T. Bondar", "Odesa", "Logistics", "118"], ["M. Kral", "Riga", "IT", "407"]]},
    {"headers": ["Order", "Date", "Total", "Status", "Courier"], "rows": [["ORD-1001", "2026-09-01", "250.00", "shipped", "Nova"], ["ORD-1002", "2026-09-02", "99.50", "pending", "Ukr"], ["ORD-1003", "2026-09-03", "1020.00", "paid", "DHL"]]},
    {"headers": ["Q", "Revenue", "Cost", "Profit"], "rows": [["Q1", "120", "80", "40"], ["Q2", "150", "95", "55"], ["Q3", "210", "120", "90"], ["Q4", "180", "110", "70"]]},
    {"headers": ["Sensor", "Value", "Unit"], "rows": [["Temp", "21.5", "C"], ["Humidity", "45", "%"], ["Pressure", "1013", "hPa"], ["CO2", "412", "ppm"], ["Noise", "38", "dB"]]},
    {"headers": ["Book", "Author", "Year", "Shelf"], "rows": [["Kobzar", "Shevchenko", "1840", "A-1"], ["Lisova", "Ukrainka", "1911", "A-2"], ["Buddenbrooks", "Mann", "1901", "B-7"]]},
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def render_text_block(text, lang, rot, blur, noise_seed):
    fp = F_ZH if lang == "zh" else F_ARIAL
    fnt = ImageFont.truetype(fp, 30, index=0) if lang == "zh" else ImageFont.truetype(fp, 30)
    im = Image.new("RGB", (IMG, IMG), (255, 255, 255))
    d = ImageDraw.Draw(im)
    # wrap
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) > 780:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    y = 300
    for ln in lines:
        d.text((58, y), ln, font=fnt, fill=(10, 10, 10))
        y += 48
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, fillcolor=(255, 255, 255))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(radius=blur))
    if noise_seed is not None:
        rng = random.Random(noise_seed)
        px = im.load()
        for _ in range(1500):
            x, y = rng.randint(0, IMG - 1), rng.randint(0, IMG - 1)
            v = rng.randint(0, 255)
            r, g, b = px[x, y]
            px[x, y] = (min(255, r + (v - 128) // 6), min(255, g + (v - 128) // 6), min(255, b + (v - 128) // 6))
    # center-crop safety to 896
    if im.size != (IMG, IMG):
        im = im.crop(((im.size[0] - IMG) // 2, (im.size[1] - IMG) // 2,
                      (im.size[0] - IMG) // 2 + IMG, (im.size[1] - IMG) // 2 + IMG))
    return im


def render_table(tbl):
    im = Image.new("RGB", (IMG, IMG), (255, 255, 255))
    d = ImageDraw.Draw(im)
    fh = ImageFont.truetype(F_ARIALB, 26)
    fc = ImageFont.truetype(F_CONSOLA, 24)
    cols = len(tbl["headers"])
    grid = [tbl["headers"]] + tbl["rows"]
    cw = 780 // cols
    x0, y = 58, 200
    for ri, row in enumerate(grid):
        for ci, cell in enumerate(row):
            x = x0 + ci * cw
            fill = (25, 55, 110) if ri == 0 else (255, 255, 255)
            d.rectangle([x, y, x + cw, y + 52], outline=(0, 0, 0), width=2, fill=fill)
            d.text((x + 10, y + 10), str(cell)[:18], font=fh if ri == 0 else fc,
                   fill=(255, 255, 255) if ri == 0 else (0, 0, 0))
        y += 52
    return im


def main():
    rng = random.Random(SEED)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    specs = []
    for i, (lang, text) in enumerate(TEXTS):
        specs.append({"kind": "text", "lang": lang, "text": text,
                      "rot": rng.choice([-3, -2, -1, 0, 1, 2, 3]) if i % 2 == 0 else 0.0,
                      "blur": rng.choice([0.0, 0.5, 0.8]) if i % 3 == 0 else 0.0,
                      "noise": 9000 + i if i % 2 == 1 else None})
    for t in TABLES:
        specs.append({"kind": "table", "lang": "en", "table": t})
    tiers = ["easy", "medium", "hard"]
    cases = []
    for i, s in enumerate(specs):
        if s["kind"] == "text":
            asset = f"text_{i:02d}_{s['lang']}.png"
            render_text_block(s["text"], s["lang"], s["rot"], s["blur"], s["noise"]).save(
                os.path.join(OUT, "assets", asset), format="PNG")
            expected = {"text": s["text"]}
            meta = {"mode": "text", "rot": s["rot"], "blur": s["blur"], "noise": s["noise"]}
        else:
            asset = f"table_{i:02d}.png"
            render_table(s["table"]).save(os.path.join(OUT, "assets", asset), format="PNG")
            expected = {"rows": [s["table"]["headers"]] + s["table"]["rows"]}
            meta = {"mode": "table", "table": s["table"]}
        cases.append({"id": f"HOME-23-{i + 1:02d}", "test_id": TEST_ID, "tier": tiers[i % 3],
                      "lang": s["lang"], "input": {"image": f"assets/{asset}", "mode": s["kind"]},
                      "expected": expected, "meta": meta})
    by = {"easy": [], "medium": [], "hard": []}
    for c in cases:
        by[c["tier"]].append(c)
    ordered = []
    for k in range(max(len(v) for v in by.values())):
        for t in tiers:
            if k < len(by[t]):
                ordered.append(by[t][k])
    for i, c in enumerate(ordered):
        c["id"] = f"HOME-23-{i + 1:02d}"
    for c in ordered:
        ap = os.path.join(OUT, c["input"]["image"])
        assert os.path.isfile(ap) and os.path.getsize(ap) > 0
        with Image.open(ap) as im2:
            assert im2.size == (IMG, IMG)
        if c["meta"]["mode"] == "text":
            assert isinstance(c["expected"]["text"], str) and len(c["expected"]["text"]) > 20
        else:
            assert len(c["expected"]["rows"]) >= 2 and all(len(r) in (3, 4, 5) for r in c["expected"]["rows"])
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
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_23.py",
                "fonts": {os.path.basename(p): sha256_file(p) for p in FONTS_USED},
                "files": files, "n_cases": len(ordered)}
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, sort_keys=True, indent=2)
    man = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    for rel, h in man["files"].items():
        assert sha256_file(os.path.join(OUT, rel)) == h, rel
    print(f"HOME-23: {len(ordered)} cases ok")


if __name__ == "__main__":
    main()
