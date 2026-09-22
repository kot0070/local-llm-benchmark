"""Unit tests for HOME-22 validator (TASK_D)."""
import json

from bench.tests import home_22 as m
from bench.types import Profile, Response


def _profile():
    return Profile(tag="qwen3.5:4b", kind="chat", caps=["text", "vision", "tools"], think="toggle",
                   ctx_max=262144, sampling={})


def _case(name="submit_form"):
    cases = m.load_cases("fixtures/HOME-22")
    assert len(cases) == 10
    return next(c for c in cases if c.expected["name"] == name)


def test_meta_binding():
    assert m.META["id"] == "HOME-22" and m.META["kind"] == "vision" and m.META["mode"] == "R0"
    assert (m.META["num_predict"], m.META["num_ctx"], m.META["timeout_s"], m.META["core_n"]) == (256, 12288, 180, 10)
    assert m.META["home"] == "qwen3.5:4b"


def test_native_gold_ok():
    c = _case()
    r = Response(content="", tool_calls=[{"name": c.expected["name"], "arguments": dict(c.expected["arguments"])}])
    v = m.validate(c, r, _profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0)
    assert v.details["channel"] == "native"


def test_textual_gold_is_format_error():
    c = _case()
    blob = json.dumps({"name": c.expected["name"], "arguments": c.expected["arguments"]})
    v = m.validate(c, Response(content="Calling tool: " + blob), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0 and v.strict == 0.0
    assert v.details["channel"] == "textual"


def test_wrong_tool_and_args():
    c = _case()
    v = m.validate(c, Response(content="", tool_calls=[{"name": "read_record", "arguments": {"record_id": "REC-1"}}]), _profile())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0
    bad_args = dict(c.expected["arguments"])
    first = next(iter(bad_args))
    bad_args[first] = "WRONG_VALUE_zzz"
    v = m.validate(c, Response(content="", tool_calls=[{"name": c.expected["name"], "arguments": bad_args}]), _profile())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0


def test_no_call_format_error():
    c = _case()
    v = m.validate(c, Response(content="I will do it later."), _profile())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0


def test_ask_user_case():
    c = _case("ask_user")
    r = Response(content="", tool_calls=[{"name": "ask_user", "arguments": c.expected["arguments"]}])
    v = m.validate(c, r, _profile())
    assert v.status == "OK"


def test_build_request_tools_and_image():
    r = m.build_request(_case(), _profile())
    assert r.tools and len(r.tools) == 6 and r.messages[0].get("images")
