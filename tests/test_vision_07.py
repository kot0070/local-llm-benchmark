"""Unit tests for HOME-07 validator (TASK_D)."""
import json

from bench.tests import home_07 as m
from bench.types import Profile, Response


def _profile():
    return Profile(tag="granite3.2-vision:2b", kind="chat", caps=["text", "vision"], think="none",
                   ctx_max=16384, sampling={})


def _case():
    cases = m.load_cases("fixtures/HOME-07")
    assert len(cases) == 16
    return cases


def test_meta_binding():
    assert m.META["id"] == "HOME-07" and m.META["kind"] == "vision" and m.META["mode"] == "R0"
    assert (m.META["num_predict"], m.META["num_ctx"], m.META["timeout_s"], m.META["core_n"]) == (120, 12288, 180, 10)
    assert m.META["home"] == "granite3.2-vision:2b"


def test_gold_ok():
    c = _case()[0]
    v = m.validate(c, Response(content=json.dumps({"answer": c.expected["answer"]})), _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0)


def test_not_present_gold():
    c = next(x for x in _case() if x.expected.get("kind") == "notpresent")
    v = m.validate(c, Response(content=json.dumps({"answer": "NOT_PRESENT"})), _profile())
    assert v.status == "OK" and v.sem == 1.0


def test_prose_wrapped_format_error():
    c = _case()[0]
    v = m.validate(c, Response(content="I found " + json.dumps({"answer": c.expected["answer"]}) + " in the doc"), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0 and v.strict == 0.0


def test_wrong_partial_empty():
    c = _case()[0]
    v = m.validate(c, Response(content=json.dumps({"answer": "DEFINITELY_NOT_THE_VALUE_zzz"})), _profile())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0
    v = m.validate(c, Response(content=""), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0


def test_build_request_has_image():
    r = m.build_request(_case()[0], _profile())
    assert r.messages[0].get("images")
