"""Unit tests for bench/validate/imagemetrics.py (TASK_D)."""
from bench.validate.imagemetrics import (
    cer, dedupe_first_table, grid_f1, iou, levenshtein, norm_ws, parse_boxes,
    parse_html_table, parse_markdown_table,
)


def test_iou_identical():
    assert iou([0, 0, 10, 10], [0, 0, 10, 10]) == 1.0


def test_iou_disjoint():
    assert iou([0, 0, 10, 10], [20, 20, 30, 30]) == 0.0


def test_iou_half():
    # half overlap horizontally: inter=50, union=150
    v = iou([0, 0, 10, 10], [5, 0, 15, 10])
    assert abs(v - 50 / 150) < 1e-9


def test_iou_degenerate():
    assert iou([5, 5, 5, 5], [0, 0, 10, 10]) == 0.0


def test_parse_boxes_gold():
    boxes = parse_boxes('[{"label": "A", "bbox_2d": [1, 2, 3, 4]}]')
    assert boxes == [{"label": "A", "bbox": [1.0, 2.0, 3.0, 4.0]}]


def test_parse_boxes_prose_and_fence():
    boxes = parse_boxes('Here you go:\n```json\n[{"label": "B", "bbox": [10, 20, 30, 40]}]\n```')
    assert len(boxes) == 1 and boxes[0]["label"] == "B"


def test_parse_boxes_single_object():
    boxes = parse_boxes('{"label": "C", "bbox_2d": [0, 0, 5, 5]}')
    assert len(boxes) == 1 and boxes[0]["bbox"] == [0.0, 0.0, 5.0, 5.0]


def test_parse_boxes_invalid():
    assert parse_boxes("no json here") == []
    assert parse_boxes('[{"label": "x"}]') == []
    assert parse_boxes('[{"label": "x", "bbox_2d": [1, 2, 3]}]') == []


def test_levenshtein_cer():
    assert levenshtein("kitten", "sitting") == 3
    assert cer("hello", "hello") == 0.0
    assert norm_ws("  a\t b ") == "a b"
    c = cer("hello world", "hello")
    assert 0.0 < c < 1.0


def test_tables():
    html = "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
    assert parse_html_table(html) == [["A", "B"], ["1", "2"]]
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    assert parse_markdown_table(md) == [["A", "B"], ["1", "2"]]
    f1, _d = grid_f1([["A", "B"], ["1", "2"]], [["A", "B"], ["1", "2"]])
    assert f1 == 1.0
    f1p, _d = grid_f1([["A", "B"], ["1", "X"]], [["A", "B"], ["1", "2"]])
    assert 0.0 < f1p < 1.0
    dup = html + " trailing prose " + html
    assert dedupe_first_table(dup).count("<table") == 1
