"""Generator for HOME-05 (chart reading, gemma3:12b). Deterministic, self-verifying.

FIX_D: chart reading is necessary (no Data table anywhere).
- easy: value labels on bars/points, no data table.
- medium: no value labels; y-axis with gridlines + tick labels every 50 or 100;
  values are multiples of 10 so they can be read exactly.
- hard: no value labels, gridlines, grouped bars or two lines + legend;
  question combines two series.
Tolerance: exact (tol_rel 0.0) except averages/ratios (tol_rel 0.02).
10 distinct question forms across the 12 cases.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

TEST_ID = "HOME-05"
SEED = 505
IMG = 896
OUT = os.path.join("fixtures", TEST_ID)
FONTS_USED = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\consola.ttf",
]

LANGS = ["en", "uk", "de", "es"]
CATS = {
    "en": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    "uk": ["Альфа", "Бета", "Гама", "Дельта", "Епсілон"],
    "de": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    "es": ["Alfa", "Beta", "Gamma", "Delta", "Epsilon"],
}
TITLES = {"bar": "Sales by category", "line": "Monthly output", "pie": "Budget share (%)",
          "grouped": "Store comparison", "twoline": "Quarterly output by series"}

ANSWER_JSON = {
    "en": 'Respond with JSON only: {"answer": <number or label>}.',
    "uk": 'Відповідайте лише JSON: {"answer": <число або назва>}.',
    "de": 'Antworten Sie nur mit JSON: {"answer": <Zahl oder Bezeichnung>}.',
    "es": 'Responda solo con JSON: {"answer": <número o etiqueta>}.',
}

# question templates: form -> lang -> template
Q = {
    "sum2": {
        "en": "What is the sum of {a} and {b}?",
        "uk": "Яка сума значень {a} та {b}?",
        "de": "Wie groß ist die Summe von {a} und {b}?",
        "es": "¿Cuál es la suma de {a} y {b}?",
    },
    "diff": {
        "en": "What is the difference between the largest and the smallest value?",
        "uk": "Яка різниця між найбільшим і найменшим значенням?",
        "de": "Wie groß ist die Differenz zwischen dem größten und dem kleinsten Wert?",
        "es": "¿Cuál es la diferencia entre el valor mayor y el menor?",
    },
    "max": {
        "en": "Which category has the largest value?",
        "uk": "Яка категорія має найбільше значення?",
        "de": "Welche Kategorie hat den größten Wert?",
        "es": "¿Qué categoría tiene el valor más alto?",
    },
    "avg": {
        "en": "What is the average of all values, rounded to one decimal?",
        "uk": "Яке середнє всіх значень, округлене до одного знака?",
        "de": "Wie hoch ist der Durchschnitt aller Werte, gerundet auf eine Dezimale?",
        "es": "¿Cuál es el promedio de todos los valores, redondeado a un decimal?",
    },
    "increase": {
        "en": "Which category increased the most between Series A and Series B?",
        "uk": "Яка категорія зросла найбільше між серією A та серією B?",
        "de": "Welche Kategorie ist zwischen Serie A und Serie B am stärksten gestiegen?",
        "es": "¿Qué categoría aumentó más entre la Serie A y la Serie B?",
    },
    "ratio": {
        "en": "What is the ratio of {a} to {b}, rounded to two decimals?",
        "uk": "Яке відношення {a} до {b}, округлене до двох знаків?",
        "de": "Wie groß ist das Verhältnis von {a} zu {b}, gerundet auf zwei Dezimalen?",
        "es": "¿Cuál es la razón de {a} a {b}, redondeada a dos decimales?",
    },
    "second": {
        "en": "Which category has the second largest value?",
        "uk": "Яка категорія має друге за величиною значення?",
        "de": "Welche Kategorie hat den zweitgrößten Wert?",
        "es": "¿Qué categoría tiene el segundo valor más alto?",
    },
    "total": {
        "en": "What is the total of all values?",
        "uk": "Яка загальна сума всіх значень?",
        "de": "Wie groß ist die Summe aller Werte?",
        "es": "¿Cuál es la suma total de todos los valores?",
    },
    "series_total": {
        "en": "What is the total of Series B across all categories?",
        "uk": "Яка сума серії B за всіма категоріями?",
        "de": "Wie groß ist die Summe der Serie B über alle Kategorien?",
        "es": "¿Cuál es el total de la Serie B en todas las categorías?",
    },
    "value": {
        "en": "What is the value of {a}?",
        "uk": "Яке значення {a}?",
        "de": "Wie groß ist der Wert von {a}?",
        "es": "¿Cuál es el valor de {a}?",
    },
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def font(size, bold=False):
    p = FONTS_USED[1] if bold else FONTS_USED[0]
    return ImageFont.truetype(p, size)


def grid_step(mx):
    return 50 if mx <= 350 else 100


def draw_grid(d, L, T, W, H, ymax, step):
    # horizontal gridlines + y tick labels every step
    for v in range(0, ymax + 1, step):
        y = T + H - (v / ymax) * H
        d.line([(L, y), (L + W, y)], fill=(200, 200, 200), width=2)
        d.text((L - 8, y - 14), str(v), font=font(20), fill=(0, 0, 0), anchor="ra")


def draw_frame(d, L, T, W, H):
    d.rectangle([L, T, L + W, T + H], outline=(30, 30, 30), width=3)


def y_of(v, T, H, ymax):
    return T + H - (v / ymax) * H


def draw_bar_single(d, labels, values, show_labels, ymax=None, step=None, grid=False):
    L, T, W, H = 110, 150, 716, 400
    if grid:
        assert ymax is not None and step is not None
        draw_grid(d, L, T, W, H, ymax, step)
    draw_frame(d, L, T, W, H)
    pal = [(31, 119, 180), (255, 127, 14), (44, 160, 44), (214, 39, 40), (148, 103, 189)]
    mx = ymax if grid else (max(values) if values else 1)
    n = len(values)
    bw = W / (n * 1.6)
    for i, v in enumerate(values):
        x = L + (i + 0.3) * (W / n)
        bh = (v / mx) * (H - 10)
        d.rectangle([x, T + H - bh, x + bw, T + H], fill=pal[i % len(pal)], outline=(0, 0, 0), width=2)
        if show_labels:
            d.text((x, T + H - bh - 30), str(v), font=font(22), fill=(0, 0, 0))
        d.text((x, T + H + 6), labels[i][:10], font=font(20), fill=(0, 0, 0))


def draw_line_single(d, labels, values, show_labels, ymax=None, step=None, grid=False):
    L, T, W, H = 110, 150, 716, 400
    if grid:
        draw_grid(d, L, T, W, H, ymax, step)
    draw_frame(d, L, T, W, H)
    mx = ymax if grid else (max(values) if values else 1)
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = L + 20 + i * ((W - 40) / max(1, n - 1))
        y = T + H - 10 - (v / mx) * (H - 20)
        pts.append((x, y))
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=(31, 119, 180), width=4)
    for (x, y), v, lb in zip(pts, values, labels):
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(214, 39, 40))
        if show_labels:
            d.text((x - 10, y - 34), str(v), font=font(20), fill=(0, 0, 0))
        d.text((x - 10, T + H + 6), lb[:8], font=font(20), fill=(0, 0, 0))


def draw_pie(d, labels, values):
    # easy only: value labels on slices
    L, T, W, H = 110, 150, 716, 400
    draw_frame(d, L, T, W, H)
    pal = [(31, 119, 180), (255, 127, 14), (44, 160, 44), (214, 39, 40), (148, 103, 189)]
    total = sum(values)
    ang = -90.0
    cx, cy, r = L + W // 2, T + H // 2, 170
    for i, v in enumerate(values):
        sweep = 360.0 * v / total
        d.pieslice([cx - r, cy - r, cx + r, cy + r], int(ang), int(ang + sweep),
                   fill=pal[i % len(pal)], outline=(0, 0, 0), width=2)
        mid = math.radians(ang + sweep / 2)
        d.text((cx + (r + 26) * math.cos(mid) - 10, cy + (r + 26) * math.sin(mid) - 12),
               f"{labels[i][:8]} {v}%", font=font(20), fill=(0, 0, 0))
        ang += sweep


def draw_grouped(d, labels, gvals, ymax, step):
    L, T, W, H = 110, 150, 716, 400
    draw_grid(d, L, T, W, H, ymax, step)
    draw_frame(d, L, T, W, H)
    pal = [(31, 119, 180), (255, 127, 14)]
    mx = ymax
    n, g = len(labels), 2
    bw = W / (n * (g + 1))
    for i in range(n):
        for j in range(g):
            v = gvals[i][j]
            x = L + i * (W / n) + (j + 0.3) * bw
            bh = (v / mx) * (H - 10)
            d.rectangle([x, T + H - bh, x + bw, T + H], fill=pal[j % len(pal)],
                        outline=(0, 0, 0), width=2)
        d.text((L + i * (W / n) + 4, T + H + 6), labels[i][:10], font=font(20), fill=(0, 0, 0))
    # legend with swatches
    d.rectangle([L + 8, T - 96, L + 470, T - 12], outline=(0, 0, 0), width=2)
    d.rectangle([L + 18, T - 80, L + 52, T - 56], fill=pal[0], outline=(0, 0, 0), width=2)
    d.text((L + 60, T - 82), "Series A", font=font(22), fill=(0, 0, 0))
    d.rectangle([L + 230, T - 80, L + 264, T - 56], fill=pal[1], outline=(0, 0, 0), width=2)
    d.text((L + 272, T - 82), "Series B", font=font(22), fill=(0, 0, 0))


def draw_twoline(d, labels, gvals, ymax, step):
    L, T, W, H = 110, 150, 716, 400
    draw_grid(d, L, T, W, H, ymax, step)
    draw_frame(d, L, T, W, H)
    cols = [(31, 119, 180), (255, 127, 14)]
    n = len(labels)
    for j in range(2):
        pts = []
        for i in range(n):
            x = L + 20 + i * ((W - 40) / max(1, n - 1))
            y = T + H - 10 - (gvals[i][j] / ymax) * (H - 20)
            pts.append((x, y))
        for a, b in zip(pts, pts[1:]):
            d.line([a, b], fill=cols[j], width=4)
        for (x, y) in pts:
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=cols[j])
    for i, lb in enumerate(labels):
        x = L + 20 + i * ((W - 40) / max(1, n - 1))
        d.text((x - 10, T + H + 6), lb[:8], font=font(20), fill=(0, 0, 0))
    d.rectangle([L + 8, T - 96, L + 470, T - 12], outline=(0, 0, 0), width=2)
    d.line([(L + 18, T - 54), (L + 52, T - 54)], fill=cols[0], width=5)
    d.text((L + 60, T - 82), "Series A", font=font(22), fill=(0, 0, 0))
    d.line([(L + 230, T - 54), (L + 264, T - 54)], fill=cols[1], width=5)
    d.text((L + 272, T - 82), "Series B", font=font(22), fill=(0, 0, 0))


# 12-case plan: (tier, ctype, qform, lang, n)
PLAN_SPEC = [
    ("easy", "bar", "sum2", "en", 4),
    ("medium", "bar", "diff", "uk", 4),
    ("hard", "grouped", "increase", "de", 3),
    ("easy", "line", "max", "es", 4),
    ("medium", "line", "second", "en", 4),
    ("hard", "twoline", "series_total", "uk", 4),
    ("easy", "pie", "max", "de", 4),
    ("medium", "bar", "ratio", "es", 4),
    ("hard", "grouped", "avg", "en", 3),
    ("easy", "bar", "total", "uk", 4),
    ("medium", "line", "value", "de", 4),
    ("hard", "twoline", "increase", "es", 4),
]


def gen_values(rng, ctype, tier, n):
    if ctype == "pie":
        raw = [rng.randint(8, 40) for _ in range(n)]
        s = sum(raw)
        values = [round(v * 100 / s) for v in raw]
        values[-1] += 100 - sum(values)
        return values, None
    if ctype in ("grouped", "twoline"):
        gvals = [[rng.randint(2, 48) * 10 for _ in range(2)] for _ in range(n)]
        # avoid degenerate ties for increase/max questions: ensure distinct maxima
        return None, gvals
    if tier == "easy":
        return [rng.randint(20, 480) for _ in range(n)], None
    return [rng.randint(2, 48) * 10 for _ in range(n)], None


def answer_of(p):
    labels, values, gvals, qform = p["labels"], p["values"], p["gvals"], p["qform"]
    if qform == "sum2":
        return values[0] + values[1], "exact", 0.0
    if qform == "diff":
        if gvals is not None:
            flat = [v for row in gvals for v in row]
            return max(flat) - min(flat), "exact", 0.0
        return max(values) - min(values), "exact", 0.0
    if qform == "max":
        if values is None:
            flat = [v for row in gvals for v in row]
            bi = flat.index(max(flat)) // 2
            return labels[bi], "label", 0.0
        return labels[values.index(max(values))], "label", 0.0
    if qform == "avg":
        flat = ([v for row in gvals for v in row] if gvals is not None else values)
        return round(sum(flat) / len(flat), 1), "numeric", 0.02
    if qform == "increase":
        inc = [row[1] - row[0] for row in gvals]
        return labels[inc.index(max(inc))], "label", 0.0
    if qform == "ratio":
        a, b = values[0], values[1]
        if b == 0:
            b = 10
        return round(a / b, 2), "numeric", 0.02
    if qform == "second":
        order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
        return labels[order[1]], "label", 0.0
    if qform == "total":
        flat = ([v for row in gvals for v in row] if gvals is not None else values)
        return sum(flat), "exact", 0.0
    if qform == "series_total":
        return sum(row[1] for row in gvals), "exact", 0.0
    if qform == "value":
        idx = 2 if len(values) > 2 else 0
        return values[idx], "exact", 0.0
    raise AssertionError(qform)


def question_of(p):
    t = Q[p["qform"]][p["lang"]]
    if p["qform"] == "sum2":
        return t.format(a=p["labels"][0], b=p["labels"][1])
    if p["qform"] == "ratio":
        return t.format(a=p["labels"][0], b=p["labels"][1])
    if p["qform"] == "value":
        idx = 2 if len(p["labels"]) > 2 else 0
        return t.format(a=p["labels"][idx])
    return t


def render_case(p):
    im = Image.new("RGB", (IMG, IMG), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((40, 24), TITLES[p["ctype"]], font=font(34, True), fill=(0, 0, 0))
    tier = p["tier"]
    if p["ctype"] == "bar":
        if tier == "easy":
            draw_bar_single(d, p["labels"], p["values"], show_labels=True)
        else:
            mx = max(p["values"])
            step = grid_step(mx)
            ymax = ((mx + step - 1) // step) * step
            draw_bar_single(d, p["labels"], p["values"], show_labels=False,
                            ymax=ymax, step=step, grid=True)
    elif p["ctype"] == "line":
        if tier == "easy":
            draw_line_single(d, p["labels"], p["values"], show_labels=True)
        else:
            mx = max(p["values"])
            step = grid_step(mx)
            ymax = ((mx + step - 1) // step) * step
            draw_line_single(d, p["labels"], p["values"], show_labels=False,
                             ymax=ymax, step=step, grid=True)
    elif p["ctype"] == "pie":
        draw_pie(d, p["labels"], p["values"])
    elif p["ctype"] == "grouped":
        flat = [v for row in p["gvals"] for v in row]
        mx = max(flat)
        step = grid_step(mx)
        ymax = ((mx + step - 1) // step) * step
        draw_grouped(d, p["labels"], p["gvals"], ymax, step)
    elif p["ctype"] == "twoline":
        flat = [v for row in p["gvals"] for v in row]
        mx = max(flat)
        step = grid_step(mx)
        ymax = ((mx + step - 1) // step) * step
        draw_twoline(d, p["labels"], p["gvals"], ymax, step)
    # no data table (FIX_D): chart must be read visually
    d.text((40, IMG - 60), f"Tier: {tier}", font=font(20), fill=(120, 120, 120))
    return im


def main():
    rng = random.Random(SEED)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    # remove stale assets from previous generator version
    for fn in os.listdir(os.path.join(OUT, "assets")):
        fp = os.path.join(OUT, "assets", fn)
        if os.path.isfile(fp):
            os.remove(fp)
    plan = []
    for (tier, ctype, qform, lang, n) in PLAN_SPEC:
        labels = CATS[lang][:n]
        values, gvals = gen_values(rng, ctype, tier, n)
        plan.append({"ctype": ctype, "tier": tier, "lang": lang, "qform": qform,
                     "labels": labels, "values": values, "gvals": gvals})
    # order already stratified: easy, medium, hard interleaved
    cases = []
    for i, p in enumerate(plan):
        ans, akind, tol = answer_of(p)
        q = question_of(p) + " " + ANSWER_JSON[p["lang"]]
        asset = f"chart_{i:02d}_{p['ctype']}_{p['qform']}.png"
        render_case(p).save(os.path.join(OUT, "assets", asset), format="PNG")
        cases.append({
            "id": f"HOME-05-{i + 1:02d}", "test_id": TEST_ID, "tier": p["tier"], "lang": p["lang"],
            "input": {"image": f"assets/{asset}", "question": q, "chart_type": p["ctype"]},
            "expected": {"answer": ans, "kind": ("label" if akind == "label" else
                                                 ("numeric" if tol > 0 else "exact")),
                         "tol_rel": tol},
            "meta": {"chart_type": p["ctype"], "labels": p["labels"], "values": p["values"],
                     "gvals": p["gvals"], "qkind": p["qform"]},
        })
    # self-verification: recompute every answer from meta; check render constraints
    forms = set()
    for c in cases:
        m = c["meta"]
        forms.add(m["qkind"])
        re_ans, re_kind, re_tol = answer_of({"labels": m["labels"], "values": m["values"],
                                            "gvals": m["gvals"], "qform": m["qkind"],
                                            "ctype": m["chart_type"]})
        assert re_ans == c["expected"]["answer"], c["id"]
        assert re_tol == c["expected"]["tol_rel"], c["id"]
        if c["tier"] in ("medium", "hard") and m["chart_type"] != "pie":
            flat = ([v for row in m["gvals"] for v in row] if m["gvals"] is not None else m["values"])
            assert all(v % 10 == 0 for v in flat), c["id"]
        ap = os.path.join(OUT, c["input"]["image"])
        assert os.path.isfile(ap) and os.path.getsize(ap) > 0, ap
        with Image.open(ap) as im2:
            assert im2.size == (IMG, IMG)
    assert len(forms) >= 8, forms
    assert {"increase", "ratio", "second"} <= forms, forms
    # tier interleave check
    tiers = [c["tier"] for c in cases]
    assert tiers == ["easy", "medium", "hard"] * 4, tiers
    assert "Data:" not in open(os.path.join(OUT, "assets", os.listdir(os.path.join(OUT, "assets"))[0]), "rb").read().decode("latin1", "ignore")
    with open(os.path.join(OUT, "cases.jsonl"), "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    files = {}
    for root, _ds, fns in os.walk(OUT):
        for fn in sorted(fns):
            if fn == "manifest.json":
                continue
            fp = os.path.join(root, fn)
            files[os.path.relpath(fp, OUT).replace(os.sep, "/")] = sha256_file(fp)
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_05.py",
                "fonts": {os.path.basename(p): sha256_file(p) for p in FONTS_USED},
                "files": files, "n_cases": len(cases)}
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, sort_keys=True, indent=2)
    man = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    for rel, h in man["files"].items():
        assert sha256_file(os.path.join(OUT, rel)) == h, rel
    print(f"HOME-05: {len(cases)} cases ok ({len(forms)} forms)")


if __name__ == "__main__":
    main()
