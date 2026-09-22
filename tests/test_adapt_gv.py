"""ADAPT_GV: plain-answer adapter for granite3.2-vision on HOME-07."""
import json

from bench.tests import home_07 as m
from bench.types import Profile, Response


def _plain_profile():
    return Profile(tag="granite3.2-vision:2b", kind="chat", caps=["text", "vision"], think="none",
                   ctx_max=16384, sampling={},
                   adapters={"tools_documented": False, "plain_answer": True},
                   profile_id="granitevision.plain_answer.v1")


def _json_profile():
    return Profile(tag="granite3.2-vision:2b", kind="chat", caps=["text", "vision"], think="none",
                   ctx_max=16384, sampling={},
                   adapters={"tools_documented": False},
                   profile_id="granitevision.pack_t0.v1")


def _cases():
    cases = m.load_cases("fixtures/HOME-07")
    assert len(cases) == 16
    return {c.id: c for c in cases}


def test_build_request_plain_strips_json_sentence():
    cases = _cases()
    c = cases["HOME-07-01"]
    assert "Respond with JSON only" in c.input["question"]
    r = m.build_request(c, _plain_profile())
    q = r.messages[0]["content"]
    assert "Respond with JSON only" not in q
    assert "Answer with the value only, in a few words, no JSON." in q
    assert "NOT_PRESENT" in q
    assert r.messages[0].get("images")


def test_build_request_plain_asserts_marker():
    c = _cases()["HOME-07-01"]
    bad = type(c)(id=c.id, test_id=c.test_id, tier=c.tier, lang=c.lang,
                  input=dict(c.input, question="What is the total?"),
                  expected=c.expected, meta=c.meta)
    try:
        m.build_request(bad, _plain_profile())
    except AssertionError:
        pass
    else:
        raise AssertionError("expected AssertionError when JSON sentence is missing")


def test_build_request_non_adapter_unchanged():
    cases = _cases()
    c = cases["HOME-07-01"]
    r = m.build_request(c, _json_profile())
    assert r.messages[0]["content"] == c.input["question"]


def test_fixtures_unchanged():
    with open("fixtures/HOME-07/cases.jsonl", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                assert "Respond with JSON only" in d["input"]["question"]


def test_plain_numeric_variants():
    c = _cases()["HOME-07-01"]  # expected 945
    p = _plain_profile()
    for text in ("945", "945 EUR", "\u20ac945", '"945"', "Answer: 945"):
        v = m.validate(c, Response(content=text), p)
        assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0), text


def test_plain_text():
    c = _cases()["HOME-07-03"]  # expected '30 days'
    v = m.validate(c, Response(content="30 days"), _plain_profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0)


def test_plain_not_present():
    c = _cases()["HOME-07-04"]
    v = m.validate(c, Response(content="NOT_PRESENT"), _plain_profile())
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0)


def test_plain_toolcall_and_doc_are_format_error():
    c = _cases()["HOME-07-01"]
    p = _plain_profile()
    v = m.validate(c, Response(content='<tool_call>[{"arguments": {"x": 1}, "name": "fetch_invoice"}]'), p)
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0 and v.strict == 0.0
    v = m.validate(c, Response(content="<doc> some dump until limit"), p)
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0 and v.strict == 0.0


def test_plain_wrong_is_wrong_answer():
    c = _cases()["HOME-07-01"]
    v = m.validate(c, Response(content="12345"), _plain_profile())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0


def test_non_adapter_json_contract_still_required():
    c = _cases()["HOME-07-01"]
    p = _json_profile()
    v = m.validate(c, Response(content=json.dumps({"answer": "945"})), p)
    assert (v.status, v.sem, v.strict) == ("OK", 1.0, 1.0)
    v = m.validate(c, Response(content="945"), p)
    assert v.status == "FORMAT_ERROR" and v.strict == 0.0
