"""Unit tests for HOME-23 validator (TASK_D)."""
from bench.tests import home_23 as m
from bench.types import Profile, Response


def _plain():
    return Profile(tag="gemma3:12b", kind="chat", caps=["text", "vision"], think="none",
                   ctx_max=131072, sampling={}, adapters={})


def _glm():
    return Profile(tag="glm-ocr:latest", kind="chat", caps=["vision", "text"], think="none",
                   ctx_max=131072, sampling={}, adapters={"glmocr_prompts": True})


def _cases():
    cases = m.load_cases("fixtures/HOME-23")
    assert len(cases) == 16
    return cases


def _text_case():
    return next(c for c in _cases() if c.input["mode"] == "text")


def _table_case():
    return next(c for c in _cases() if c.input["mode"] == "table")


def test_meta_binding():
    assert m.META["id"] == "HOME-23" and m.META["kind"] == "vision" and m.META["mode"] == "R0"
    assert (m.META["num_predict"], m.META["num_ctx"], m.META["timeout_s"], m.META["core_n"]) == (1024, 12288, 180, 10)
    assert m.META["think_extra"] == 0 and m.META["home"] == "glm-ocr:latest"


def test_text_gold_ok():
    c = _text_case()
    v = m.validate(c, Response(content=c.expected["text"]), _plain())
    assert v.status == "OK" and v.sem == 1.0


def test_text_partial_wrong():
    c = _text_case()
    hyp = c.expected["text"][: len(c.expected["text"]) // 2] + " zzzqqq " + c.expected["text"][len(c.expected["text"]) // 2:]
    v = m.validate(c, Response(content=hyp), _plain())
    assert v.status == "WRONG_ANSWER" and 0.0 < v.sem < 1.0


def test_text_empty_format_error():
    v = m.validate(_text_case(), Response(content=""), _plain())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0


def test_table_gold_ok():
    c = _table_case()
    rows = c.expected["rows"]
    html = "<table>" + "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in r) + "</tr>" for r in rows) + "</table>"
    v = m.validate(c, Response(content=html), _plain())
    assert v.status == "OK" and v.sem == 1.0


def test_table_partial_and_dedupe():
    c = _table_case()
    rows = [list(r) for r in c.expected["rows"]]
    rows[1][0] = "TOTALLY_WRONG_CELL_zzz"
    html = "<table>" + "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in r) + "</tr>" for r in rows) + "</table>"
    v = m.validate(c, Response(content=html), _plain())
    assert v.status == "WRONG_ANSWER" and 0.0 < v.sem < 1.0
    good = "<table><tr><td>" + "</td></tr></table>"
    rows0 = c.expected["rows"]
    one = "<table>" + "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in r) + "</tr>" for r in rows0) + "</table>"
    v = m.validate(c, Response(content=one + " repeated junk " + one), _plain())
    assert v.status == "OK"


def test_glmocr_prompts_and_stop():
    rt = m.build_request(_text_case(), _glm())
    assert rt.messages[0]["content"] == "Text Recognition:"
    assert rt.options.get("stop") == ["\n```"]
    assert rt.messages[0].get("images")
    rt = m.build_request(_table_case(), _glm())
    assert rt.messages[0]["content"] == "Table Recognition:"
    ro = m.build_request(_text_case(), _plain())
    assert "Transcribe" in ro.messages[0]["content"]
    ro = m.build_request(_table_case(), _plain())
    assert "<table>" in ro.messages[0]["content"]
