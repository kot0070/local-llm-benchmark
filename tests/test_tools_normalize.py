"""Unit tests for toolsx.normalize_calls / args_equal (owner: TASK_C)."""
from bench.types import Response
from bench.validate.toolsx import normalize_calls, args_equal


def _resp(content="", calls=None):
    return Response(content=content, tool_calls=calls or [])


def test_native_single():
    r = _resp("", [{"name": "get_weather", "arguments": {"city": "Paris", "unit": "celsius"}}])
    calls, ch = normalize_calls(r)
    assert ch == "native"
    assert calls == [{"name": "get_weather", "arguments": {"city": "Paris", "unit": "celsius"}}]


def test_native_openai_shape():
    r = _resp("", [{"function": {"name": "get_weather", "arguments": '{"city": "Paris"}'}}])
    calls, ch = normalize_calls(r)
    assert ch == "native"
    assert calls[0]["name"] == "get_weather"
    assert calls[0]["arguments"] == {"city": "Paris"}


def test_textual_detected():
    r = _resp('I will call {"name": "get_weather", "arguments": {"city": "Paris"}} now.')
    calls, ch = normalize_calls(r)
    assert ch == "textual"
    assert calls[0]["name"] == "get_weather"


def test_none_channel():
    r = _resp("Hello, no tools here.")
    calls, ch = normalize_calls(r)
    assert ch == "none" and calls == []


def test_args_equal_numbers():
    eq, det = args_equal({"amount": 5}, {"amount": 5.0},
                         {"type": "object", "properties": {"amount": {"type": "number"}}})
    assert eq and not det["whitespace_padded"]


def test_args_equal_whitespace():
    eq, det = args_equal({"city": "  Paris "}, {"city": "Paris"},
                         {"type": "object", "properties": {"city": {"type": "string"}}})
    assert eq and det["whitespace_padded"]


def test_args_equal_extra_keys():
    eq, det = args_equal({"a": 1, "b": 2}, {"a": 1}, None)
    assert not eq and det["extra_keys"] == ["b"]


def test_args_equal_missing():
    eq, det = args_equal({"a": 1}, {"a": 1, "b": 2}, None)
    assert not eq and det["missing_keys"] == ["b"]


def test_args_equal_bool_strict():
    eq, _ = args_equal({"x": True}, {"x": 1}, None)
    assert not eq
