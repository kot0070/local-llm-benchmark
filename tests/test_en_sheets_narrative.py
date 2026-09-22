"""Tests for tools/en_sheets_narrative.py (DEEP_SHEETS_NARRATIVE)."""
import json
import os
import re
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.en_sheets_narrative import (  # noqa: E402
    NOT_AVAILABLE,
    SHEET_NAMES_NARRATIVE,
    build_all_narrative,
    build_recommendations_sheet,
    build_scorecard_sheet,
    build_strengths_sheet,
    load_analysis,
)

ANALYSIS_DIR = os.path.join(ROOT, "analysis_en")

CYRILLIC = re.compile(r"[\u0400-\u04FF]")
# British-specific stems. 'analys' excludes US 'analysis/analyses/analyst',
# which share the root but are spelled the same in US English; 'organis'
# needs no exclusion ('organize' uses z, so the 'organis' stem only matches
# British 'organise/organisation').
BRITISH = re.compile(
    r"optimis|behaviour|organis|centre|licence|programme|favour|colour"
    r"|analys(?!is\b|es\b|t\b)",
    re.IGNORECASE,
)


def _cells_of(ws):
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value:
                yield cell.value


def _synthetic():
    full = {
        "model": "alpha:1b",
        "profile": {
            "documented": "A small test model documented for text tasks.",
            "role_in_run": "Its home test covers text classification.",
        },
        "overall": {
            "rating_10": 7.5,
            "tests_scored": 6,
            "rating_basis": "Mean 0.800 across 6 tests combine to 7.5.",
        },
        "use_when": ["Classifying short messages", "Routing tickets"],
        "avoid_when": ["Long reasoning chains"],
        "strengths": ["Scores well on short texts."],
        "weaknesses": ["Fails on long contexts."],
        "hardware_fit": "Runs fully on the GPU at about 90 tokens/s.",
        "bottom_line": "A fast generalist for short-text work.",
    }
    sparse = {
        "model": "beta:2b",
        "profile": {},
        "overall": {"rating_10": 9.1, "tests_scored": 1},
        "use_when": [],
        "avoid_when": None,
        "strengths": ["No strengths observed in this run."],
        "weaknesses": ["Misses 2 of the unsafe cases by labeling them safe."],
        "hardware_fit": "",
        "bottom_line": None,
    }
    return [full, sparse]


def test_load_analysis_merges_24_sorted():
    analysis = load_analysis(ANALYSIS_DIR)
    assert len(analysis) == 24
    tags = [m["model"] for m in analysis]
    assert len(set(tags)) == 24
    assert tags == sorted(tags)


def test_load_analysis_raises_on_duplicate_or_missing(tmp_path):
    good = {
        "model": "m:1", "profile": {}, "overall": {},
        "use_when": [], "avoid_when": [], "strengths": [],
        "weaknesses": [], "hardware_fit": "", "bottom_line": "",
    }
    for name in ("group_a.json", "group_b.json", "group_c.json",
                 "group_d.json"):
        with open(os.path.join(str(tmp_path), name), "w",
                   encoding="utf-8") as f:
            json.dump([dict(good, model="%s-%s" % (name, i))
                       for i in range(6)], f)
    assert len(load_analysis(str(tmp_path))) == 24
    # Duplicate one model tag across two groups.
    dup_path = os.path.join(str(tmp_path), "group_b.json")
    with open(dup_path, encoding="utf-8") as f:
        group_b = json.load(f)
    group_b[0]["model"] = "group_a.json-0"
    with open(dup_path, "w", encoding="utf-8") as f:
        json.dump(group_b, f)
    with pytest.raises(ValueError):
        load_analysis(str(tmp_path))
    # Missing group file.
    os.remove(os.path.join(str(tmp_path), "group_d.json"))
    with pytest.raises(ValueError):
        load_analysis(str(tmp_path))


def _scorecard_rows(ws):
    """Return (band_labels, data_rows); data rows are lists of values."""
    bands = []
    data = []
    for row in ws.iter_rows(min_row=4, values_only=True):
        if row[0] is None:
            continue
        rest_empty = all(v is None for v in row[1:])
        if rest_empty:
            bands.append(row[0])
        else:
            data.append(list(row))
    return bands, data


def test_real_sheets_shape_and_sort():
    import openpyxl

    analysis = load_analysis(ANALYSIS_DIR)
    wb = openpyxl.Workbook()
    build_all_narrative(wb, analysis)
    assert wb.sheetnames[1:] == SHEET_NAMES_NARRATIVE

    ws = wb[SHEET_NAMES_NARRATIVE[0]]
    bands, data = _scorecard_rows(ws)
    assert bands == [
        "Generalist models (5 or more tests scored)",
        "Focused models (2 to 4 tests scored)",
        "Single-test models (1 test scored)",
    ]
    assert len(data) == 24
    for row in data:
        assert all(v is not None and str(v).strip() for v in row)
        assert isinstance(row[1], (int, float)) and 0.0 <= row[1] <= 10.0
        assert isinstance(row[2], int)
    by_tag = {m["model"]: m for m in analysis}
    # Tier membership and descending rating within each tier.
    current_band = None
    last_rating = None
    for row, band_row in _walk_scorecard(ws):
        if band_row is not None:
            current_band = band_row
            last_rating = None
            continue
        tag = row[0]
        n = by_tag[tag]["overall"]["tests_scored"]
        expect_cov = ("Generalist (5+ tests)" if n >= 5
                      else "Focused (2-4 tests)" if n >= 2
                      else "Single-test (1 test)")
        assert row[3] == expect_cov
        assert current_band is not None
        assert expect_cov.split(" ")[0] in current_band
        if last_rating is not None:
            assert row[1] <= last_rating
        last_rating = row[1]

    for title in SHEET_NAMES_NARRATIVE[1:]:
        ws2 = wb[title]
        rows = [list(r) for r in ws2.iter_rows(min_row=2, values_only=True)
                if r[0] is not None]
        assert len(rows) == 24
        for row in rows:
            assert all(v is not None and str(v).strip() for v in row)
        tags = [r[0] for r in rows]
        assert tags == sorted(tags)


def _walk_scorecard(ws):
    """Yield (row_values, band_label_or_None) in sheet order."""
    for row in ws.iter_rows(min_row=4, values_only=True):
        if row[0] is None:
            continue
        if all(v is None for v in row[1:]):
            yield list(row), row[0]
        else:
            yield list(row), None


def test_synthetic_bullets_and_fallbacks():
    import openpyxl

    wb = openpyxl.Workbook()
    build_recommendations_sheet(wb, _synthetic())
    ws = wb[SHEET_NAMES_NARRATIVE[1]]
    rows = {r[0].value: r for r in ws.iter_rows(min_row=2) if r[0].value}
    full_use = rows["alpha:1b"][1].value
    assert full_use == "\u2022 Classifying short messages\n\u2022 Routing tickets"
    assert rows["alpha:1b"][1].alignment.wrap_text is True
    assert rows["alpha:1b"][1].alignment.vertical == "top"
    assert rows["beta:2b"][1].value == NOT_AVAILABLE
    assert rows["beta:2b"][2].value == NOT_AVAILABLE
    assert rows["beta:2b"][3].value == NOT_AVAILABLE

    wb2 = openpyxl.Workbook()
    build_strengths_sheet(wb2, _synthetic())
    ws2 = wb2[SHEET_NAMES_NARRATIVE[2]]
    rows2 = {r[0].value: r for r in ws2.iter_rows(min_row=2) if r[0].value}
    # Single honest 'none observed' sentence renders plainly, no bullet.
    assert rows2["beta:2b"][1].value == "No strengths observed in this run."
    # Any other single-item list keeps its bullet.
    assert rows2["beta:2b"][2].value.startswith("\u2022 ")
    assert rows2["alpha:1b"][1].value.startswith("\u2022 ")

    wb3 = openpyxl.Workbook()
    build_scorecard_sheet(wb3, _synthetic())
    _, data = _scorecard_rows(wb3[SHEET_NAMES_NARRATIVE[0]])
    beta = next(r for r in data if r[0] == "beta:2b")
    assert beta[4] == NOT_AVAILABLE  # rating_basis missing
    assert beta[5] == NOT_AVAILABLE  # documented missing
    assert beta[7] == NOT_AVAILABLE  # bottom_line missing


def test_no_cyrillic_in_rendered_cells():
    import openpyxl

    wb = openpyxl.Workbook()
    build_all_narrative(wb, load_analysis(ANALYSIS_DIR))
    hits = [(t, v) for t in wb.sheetnames for v in _cells_of(wb[t])
            if CYRILLIC.search(v)]
    assert hits == []


def _json_sources(analysis):
    srcs = []
    for m in analysis:
        overall = m.get("overall") or {}
        profile = m.get("profile") or {}
        for v in [profile.get("documented"), profile.get("role_in_run"),
                  overall.get("rating_basis"), m.get("hardware_fit"),
                  m.get("bottom_line")]:
            if isinstance(v, str) and v.strip():
                srcs.append(v)
        for key in ("strengths", "weaknesses", "use_when", "avoid_when"):
            for v in m.get(key) or []:
                if isinstance(v, str) and v.strip():
                    srcs.append(v)
    return srcs


def test_british_scan_only_flags_json_content():
    import openpyxl

    # The scan itself is not vacuous: it catches known British forms and
    # lets US spellings through.
    assert BRITISH.search("optimisation")
    assert BRITISH.search("behaviours")
    assert BRITISH.search("favours rapid work")
    assert not BRITISH.search("analysis of the results")
    assert not BRITISH.search("organize the schedule")
    assert not BRITISH.search("the data center license")

    analysis = load_analysis(ANALYSIS_DIR)
    wb = openpyxl.Workbook()
    build_all_narrative(wb, analysis)
    srcs = _json_sources(analysis)
    flagged = [(t, v) for t in wb.sheetnames for v in _cells_of(wb[t])
               if BRITISH.search(v)]
    # Every hit must be traceable to an input JSON string (flagged, not
    # fixed: JSON wording is the writers' responsibility). Nothing added by
    # this module may introduce a hit.
    assert flagged, "expected at least the known JSON 'optimisation' hits"
    for title, value in flagged:
        assert any(_trace_hit(value, s) for s in srcs), (title, value)


def _trace_hit(cell_value, source):
    m = BRITISH.search(cell_value)
    if not m:
        return False
    hit = m.group(0).lower()
    return hit in source.lower() and source.strip() in cell_value


def test_determinism_cell_values():
    import openpyxl

    analysis = load_analysis(ANALYSIS_DIR)
    wb1 = openpyxl.Workbook()
    build_all_narrative(wb1, analysis)
    wb2 = openpyxl.Workbook()
    build_all_narrative(wb2, analysis)
    assert wb1.sheetnames == wb2.sheetnames
    for title in wb1.sheetnames:
        v1 = [[c.value for c in row] for row in wb1[title].iter_rows()]
        v2 = [[c.value for c in row] for row in wb2[title].iter_rows()]
        assert v1 == v2
