"""Unit tests for TASK_B2 validators home_01/03/08/12/16/19 (owner: TASK_B2)."""
import json

import pytest

from bench.types import Case, Profile, Response

from bench.tests import home_01, home_03, home_08, home_12, home_16, home_19


def prof(tag="test-model", **kw):
    base = dict(tag=tag, kind="chat", caps=["text"], think="none", ctx_max=8192,
                sampling={}, adapters={}, stop=[], system=None,
                embed_prefix={}, profile_id="t", notes="")
    base.update(kw)
    return Profile(**base)


def resp(content):
    return Response(content=content)


def gold_case(mod, **over):
    cases = mod.load_cases("fixtures/" + mod.META["id"])
    assert len(cases) > 0
    return cases[0]


# ---------------- HOME-01 ----------------

def _score(per_field, name):
    v = per_field[name]
    return v.get("score", 0.0) if isinstance(v, dict) else float(v)


def test_h01_gold_ok():
    c = gold_case(home_01)
    p = prof()
    r = resp(json.dumps(c.expected, ensure_ascii=False))
    v = home_01.validate(c, r, p)
    assert v.status == "OK" and v.sem == 1.0 and v.strict == 1.0


def test_h01_empty_format():
    c = gold_case(home_01)
    v = home_01.validate(c, resp(""), prof())
    assert v.status == "FORMAT_ERROR" and v.sem == 0.0


def test_h01_prose_format_but_sem():
    c = gold_case(home_01)
    r = resp("Here is the result:\n" + json.dumps(c.expected) + "\nHope this helps.")
    v = home_01.validate(c, r, prof())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0 and v.strict == 0.0


def test_h01_wrong_answer():
    c = gold_case(home_01)
    bad = dict(c.expected, intent="refund" if c.expected["intent"] != "refund" else "complaint")
    v = home_01.validate(c, resp(json.dumps(bad)), prof())
    assert v.status == "WRONG_ANSWER" and v.sem < 1.0


def test_h01_partial_field():
    c = gold_case(home_01)
    partial = dict(c.expected)
    partial.pop("urgency")
    v = home_01.validate(c, resp(json.dumps(partial)), prof())
    assert v.status == "WRONG_ANSWER" and 0.0 < v.sem < 1.0
    assert _score(v.details["per_field"], "urgency") == 0.0


def test_h01_build_request_contract():
    c = gold_case(home_01)
    req = home_01.build_request(c, prof())
    assert req.endpoint == "chat" and len(req.messages) == 2
    assert "entity_ids" in req.messages[0]["content"]


# ---------------- HOME-03 ----------------

def test_h03_gold_ok():
    c = gold_case(home_03)
    v = home_03.validate(c, resp(json.dumps(c.expected)), prof())
    assert v.status == "OK" and v.sem == 1.0


def test_h03_empty_format():
    c = gold_case(home_03)
    v = home_03.validate(c, resp(""), prof())
    assert v.status == "FORMAT_ERROR"


def test_h03_wrong_answer():
    c = gold_case(home_03)
    bad = {"answer": "definitely not in the documents", "citations": [], "abstain": False}
    v = home_03.validate(c, resp(json.dumps(bad)), prof())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0


def test_h03_unanswerable_gold():
    cases = home_03.load_cases("fixtures/HOME-03")
    un = [c for c in cases if c.expected.get("answer") is None]
    assert len(un) == 3
    c = un[0]
    v = home_03.validate(c, resp(json.dumps(c.expected)), prof())
    assert v.status == "OK" and v.sem == 1.0
    # answering instead of abstaining fails
    bad = {"answer": "some guess", "citations": ["D1"], "abstain": False}
    v2 = home_03.validate(c, resp(json.dumps(bad)), prof())
    assert v2.status == "WRONG_ANSWER"


def test_h03_citation_scores():
    c = gold_case(home_03)
    good = dict(c.expected)
    v = home_03.validate(c, resp(json.dumps(good)), prof())
    assert v.details["citation_f1"] == 1.0
    nocite = dict(good, citations=[])
    v2 = home_03.validate(c, resp(json.dumps(nocite)), prof())
    assert v2.status == "OK" and v2.details["citation_f1"] == 0.0  # answer still right


def _find_case_by_topic(topic: str):
    cases = home_03.load_cases("fixtures/HOME-03")
    for c in cases:
        q = (c.input.get("question", "") or "").lower()
        if topic == "price_warranty" and "vacuum hv-90" in q and "warranty" in q:
            return c
    raise AssertionError("synth case not found")


def test_h03_paraphrase_synth_ok():
    cases = home_03.load_cases("fixtures/HOME-03")
    synth = [c for c in cases if len(c.expected.get("facts", [])) >= 2]
    assert synth, "no multi-fact case"
    # prefer the price_warranty case with 189 usd for a stable paraphrase
    c = next((x for x in synth if any("189" in f for f in x.expected["facts"])), synth[0])
    facts = c.expected["facts"]
    # paraphrased: $ sign, plural units, different wording
    if any("189" in f for f in facts):
        para = "The HV-90 costs $189 and comes with a 3 years warranty."
    elif any("29" in f for f in facts):
        para = "Extended warranty costs $29 with service at central depot."
    else:
        para = "Support hours are 8:00 to 18:00 and contact care@helios.example."
        # ensure 8:00-18:00 split still matches all three facts
        assert set(facts) == {"8:00", "18:00", "care@helios.example"}
    good = {"answer": para, "citations": c.expected["citations"], "abstain": False}
    v = home_03.validate(c, resp(json.dumps(good)), prof())
    assert v.status == "OK" and v.sem == 1.0, v.details


def test_h03_paraphrase_missing_fact_fails():
    cases = home_03.load_cases("fixtures/HOME-03")
    synth = [c for c in cases if len(c.expected.get("facts", [])) >= 2][0]
    facts = synth.expected["facts"]
    # mention only the first fact, drop the second
    if any("189" in f for f in facts):
        para = "The HV-90 costs 189 USD."
    else:
        para = "Support hours are 8:00 to 18:00 on weekdays."
    good = {"answer": para, "citations": synth.expected["citations"], "abstain": False}
    v = home_03.validate(synth, resp(json.dumps(good)), prof())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0


def test_h03_single_fact_normalization():
    cases = home_03.load_cases("fixtures/HOME-03")
    single = [c for c in cases if c.expected.get("facts") == ["30 day"]]
    assert single, "30-day case missing"
    c = single[0]
    for variant in ("30 days", "30-day", "30 day"):
        good = {"answer": f"Return window is {variant}.", "citations": c.expected["citations"], "abstain": False}
        v = home_03.validate(c, resp(json.dumps(good)), prof())
        assert v.status == "OK" and v.sem == 1.0, (variant, v.details)


# ---------------- HOME-08 ----------------

def test_h08_json_gold_ok():
    cases = home_08.load_cases("fixtures/HOME-08")
    c = cases[0]
    v = home_08.validate(c, resp(json.dumps(c.expected)), prof())
    assert v.status == "OK" and v.sem == 1.0


def test_h08_json_wrong_label():
    cases = home_08.load_cases("fixtures/HOME-08")
    c = cases[0]
    flip = "unsafe" if c.expected["label"] == "safe" else "safe"
    bad = {"label": flip, "categories": []}
    v = home_08.validate(c, resp(json.dumps(bad)), prof())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0


def test_h08_json_empty():
    c = gold_case(home_08)
    v = home_08.validate(c, resp(""), prof())
    assert v.status == "FORMAT_ERROR"


def test_h08_raw_adapter_request():
    c = gold_case(home_08)
    p = prof(tag="llama-guard3:8b", adapters={"llamaguard_raw": True})
    req = home_08.build_request(c, p)
    assert req.endpoint == "generate" and req.raw is True
    assert "<BEGIN UNSAFE CONTENT CATEGORIES>" in req.prompt
    assert "S12: Sexual Content." in req.prompt


def test_h08_raw_validate():
    cases = home_08.load_cases("fixtures/HOME-08")
    p = prof(tag="llama-guard3:8b", adapters={"llamaguard_raw": True})
    unsafe = [c for c in cases if c.expected["label"] == "unsafe"][0]
    cats = ",".join(unsafe.expected["categories"])
    v = home_08.validate(unsafe, resp("unsafe\n" + cats), p)
    assert v.status == "OK" and v.sem == 1.0 and v.details["category_exact"] == 1.0
    safe = [c for c in cases if c.expected["label"] == "safe"][0]
    v2 = home_08.validate(safe, resp("safe"), p)
    assert v2.status == "OK"
    v3 = home_08.validate(safe, resp(""), p)
    assert v3.status == "FORMAT_ERROR"


# ---------------- HOME-12 ----------------

def test_h12_gold_ok():
    c = gold_case(home_12)
    v = home_12.validate(c, resp(json.dumps(c.expected, ensure_ascii=False)), prof())
    assert v.status == "OK" and v.sem == 1.0


def test_h12_empty_format():
    c = gold_case(home_12)
    v = home_12.validate(c, resp("   "), prof())
    assert v.status == "FORMAT_ERROR"


def test_h12_partial():
    c = gold_case(home_12)
    got = json.loads(json.dumps(c.expected))
    # corrupt one leaf value
    def corrupt(o):
        if isinstance(o, dict):
            for k in o:
                if isinstance(o[k], str) and o[k] not in ("",):
                    o[k] = o[k] + " CORRUPTED"
                    return True
                if corrupt(o[k]):
                    return True
        elif isinstance(o, list):
            for v in o:
                if corrupt(v):
                    return True
        return False
    assert corrupt(got)
    v = home_12.validate(c, resp(json.dumps(got)), prof())
    assert v.status == "WRONG_ANSWER" and 0.0 < v.sem < 1.0


def test_h12_raw_request():
    c = gold_case(home_12)
    p = prof(tag="nuextract:3.8b", adapters={"nuextract_raw": True})
    req = home_12.build_request(c, p)
    assert req.endpoint == "generate" and req.raw is True
    assert req.prompt.startswith("<|input|>\n### Template:\n")
    assert "\n<|output|>\n" in req.prompt
    assert "<|end-output|>" in req.options.get("stop", [])


# ---------------- HOME-16 ----------------

def test_h16_gold_ok():
    c = gold_case(home_16)
    v = home_16.validate(c, resp(json.dumps(c.expected)), prof())
    assert v.status == "OK" and v.sem == 1.0


def test_h16_policy_identical():
    import hashlib
    cases = home_16.load_cases("fixtures/HOME-16")
    assert len(cases) == 40
    hashes = {c.meta.get("policy_sha256") for c in cases}
    assert len(hashes) == 1 and None not in hashes
    pols = {c.input.get("policy") for c in cases}
    assert len(pols) == 1
    only = next(iter(pols))
    assert "suicide,5" not in only
    assert hashlib.sha256(only.encode("utf-8")).hexdigest() == next(iter(hashes))
    hard = [c for c in cases if c.tier == "hard"]
    assert len(hard) >= 10


def test_h16_wrong_route():
    c = gold_case(home_16)
    other = "BILLING" if c.expected["route"] != "BILLING" else "TECH"
    v = home_16.validate(c, resp(json.dumps({"route": other, "reason_code": "X"})), prof())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0


def test_h16_prose_format():
    c = gold_case(home_16)
    v = home_16.validate(c, resp("I think it is " + json.dumps(c.expected)), prof())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0


def test_h16_empty():
    c = gold_case(home_16)
    assert home_16.validate(c, resp(""), prof()).status == "FORMAT_ERROR"


# ---------------- HOME-19 ----------------

def test_h19_gold_ok():
    cases = home_19.load_cases("fixtures/HOME-19")
    c = cases[0]
    v = home_19.validate(c, resp(c.expected["markdown"]), prof())
    assert v.status == "OK" and v.sem == 1.0


def test_h19_fenced_format():
    c = home_19.load_cases("fixtures/HOME-19")[0]
    v = home_19.validate(c, resp("```markdown\n" + c.expected["markdown"] + "\n```"), prof())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0 and v.strict == 0.0


def test_h19_wrong_content():
    c = home_19.load_cases("fixtures/HOME-19")[0]
    v = home_19.validate(c, resp("# Totally different\n\nNothing in common xyzzy.\n"), prof())
    assert v.status == "WRONG_ANSWER" and v.sem < 0.5


def test_h19_empty():
    c = home_19.load_cases("fixtures/HOME-19")[0]
    v = home_19.validate(c, resp(""), prof())
    assert v.status in ("WRONG_ANSWER", "FORMAT_ERROR") and v.sem == 0.0


def test_h19_reader_request():
    c = home_19.load_cases("fixtures/HOME-19")[0]
    p = prof(tag="reader-lm:1.5b", adapters={"reader_raw_html": True})
    req = home_19.build_request(c, p)
    assert req.messages[0]["content"] == c.input["html"]
    req2 = home_19.build_request(c, prof())
    assert "Markdown" in req2.messages[0]["content"]


def test_meta_values():
    assert home_01.META["num_predict"] == 256 and home_01.META["core_n"] == 12
    assert home_03.META["num_predict"] == 300 and home_03.META["num_ctx"] == 8192
    assert home_08.META["num_predict"] == 160 and home_08.META["timeout_s"] == 90
    assert home_12.META["num_predict"] == 768 and home_12.META["think_extra"] == 1536
    assert home_16.META["num_predict"] == 64 and home_16.META["core_n"] == 20
    assert home_19.META["num_predict"] == 3000 and home_19.META["num_ctx"] == 12288
