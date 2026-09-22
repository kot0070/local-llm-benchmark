"""Unit tests for HOME-15 validator (TASK_D)."""
import json

from bench.tests import home_15 as m
from bench.types import Profile, Response


def _profile(adapters=None):
    return Profile(tag="qwen2.5vl:7b", kind="chat", caps=["text", "vision"], think="none",
                   ctx_max=128000, sampling={}, adapters=adapters or {})


def _case():
    cases = m.load_cases("fixtures/HOME-15")
    assert len(cases) == 12
    return cases


def test_meta_binding():
    assert m.META["id"] == "HOME-15" and m.META["kind"] == "vision" and m.META["mode"] == "R0"
    assert (m.META["num_predict"], m.META["num_ctx"], m.META["timeout_s"], m.META["core_n"]) == (256, 12288, 180, 12)
    assert m.META["home"] == "qwen2.5vl:7b"


def test_gold_ok():
    c = _case()[0]
    body = json.dumps([{"label": c.expected["label"], "bbox_2d": c.expected["bbox"]}])
    v = m.validate(c, Response(content=body), _profile({"grounding_coords": "absolute_px"}))
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0)
    assert v.details["iou"] == 1.0


def test_rel1000_converted():
    c = _case()[0]
    x1, y1, x2, y2 = c.expected["bbox"]
    rel = [x1 / 896 * 1000, y1 / 896 * 1000, x2 / 896 * 1000, y2 / 896 * 1000]
    body = json.dumps([{"label": c.expected["label"], "bbox_2d": rel}])
    v = m.validate(c, Response(content=body), _profile({"grounding_coords": "rel_1000"}))
    assert v.status == "OK" and v.details["iou"] >= 0.99


def test_far_box_wrong():
    c = _case()[0]
    body = json.dumps([{"label": "elsewhere", "bbox_2d": [700, 700, 800, 800]}])
    v = m.validate(c, Response(content=body), _profile({"grounding_coords": "absolute_px"}))
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0


def test_prose_wrapped_and_empty():
    c = _case()[0]
    body = json.dumps([{"label": c.expected["label"], "bbox_2d": c.expected["bbox"]}])
    v = m.validate(c, Response(content="Found it: " + body), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0 and v.strict == 0.0
    v = m.validate(c, Response(content=""), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0


def test_prompt_adapters():
    c = _case()[0]
    r = m.build_request(c, _profile({"grounding_coords": "absolute_px"}))
    assert "PIXEL" in r.messages[0]["content"] and r.messages[0].get("images")
    r = m.build_request(c, _profile({"grounding_coords": "rel_1000"}))
    assert "0-1000" in r.messages[0]["content"]
    r = m.build_request(c, _profile())
    assert "896x896" in r.messages[0]["content"]
