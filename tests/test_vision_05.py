"""Unit tests for HOME-05 validator (TASK_D)."""
import json

from bench.tests import home_05 as m
from bench.types import Profile, Response


def _profile(tag="gemma3:12b"):
    return Profile(tag=tag, kind="chat", caps=["text", "vision"], think="none", ctx_max=131072, sampling={})


def _case():
    cases = m.load_cases("fixtures/HOME-05")
    assert len(cases) == 12
    return cases


def _resp(text):
    return Response(content=text)


def test_meta_binding():
    assert m.META["id"] == "HOME-05" and m.META["kind"] == "vision" and m.META["mode"] == "R0"
    assert (m.META["num_predict"], m.META["num_ctx"], m.META["timeout_s"], m.META["core_n"]) == (200, 12288, 240, 8)
    assert m.META["think_extra"] == 1024 and m.META["home"] == "gemma3:12b"


def test_gold_numeric_and_label():
    num = next(c for c in _case() if c.expected["kind"] != "label")
    v = m.validate(num, _resp(json.dumps({"answer": num.expected["answer"]})), _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0)
    lab = next(c for c in _case() if c.expected["kind"] == "label")
    v = m.validate(lab, _resp(json.dumps({"answer": lab.expected["answer"]})), _profile())
    assert v.status == "OK" and v.sem == 1.0


def test_prose_wrapped_gold_is_format_error():
    c = _case()[0]
    v = m.validate(c, _resp("The answer is " + json.dumps({"answer": c.expected["answer"]}) + " hope it helps"), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0 and v.strict == 0.0


def test_fenced_is_format_error():
    c = _case()[0]
    v = m.validate(c, _resp("```json\n" + json.dumps({"answer": c.expected["answer"]}) + "\n```"), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0


def test_wrong_and_empty():
    num = next(c for c in _case() if c.expected["kind"] != "label")
    bad = (num.expected["answer"] + 999) if isinstance(num.expected["answer"], (int, float)) else "nope"
    v = m.validate(num, _resp(json.dumps({"answer": bad})), _profile())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0
    v = m.validate(num, _resp(""), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0
    v = m.validate(num, _resp("not json at all"), _profile())
    assert v.status == "FORMAT_ERROR"


def test_non_english_granite_unsupported():
    non_en = [c for c in _case() if c.lang != "en"]
    assert non_en, "fixture set must contain non-en cases"
    v = m.validate(non_en[0], _resp(json.dumps({"answer": 1})), _profile("granite3.2-vision:2b"))
    assert v.status == "UNSUPPORTED_CAPABILITY" and v.sub_reason == "LANGUAGE_NOT_DOCUMENTED"


def test_build_request_has_image():
    c = _case()[0]
    r = m.build_request(c, _profile())
    assert r.endpoint == "chat" and r.messages and r.messages[0].get("images")
    assert len(r.messages[0]["images"][0]) > 1000
