"""Validator tests for all TASK_C homes (owner: TASK_C)."""
import json
import os

from bench.types import Case, Profile, Request, Response

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "fixtures")


def _prof(**kw):
    return Profile(tag=kw.get("tag", "test"), kind=kw.get("kind", "chat"), caps=[],
                   think="none", ctx_max=8192, sampling={}, profile_id="t",
                   system=None, embed_prefix=kw.get("embed_prefix", {}), notes="")


# ---- HOME-09 ----
def _h09_case():
    import bench.tests.home_09 as h
    cases = h.load_cases(os.path.join(FIX, "HOME-09"))
    assert len(cases) == 8
    return cases[0]


def test_h09_gold():
    import bench.tests.home_09 as h
    c = _h09_case()
    gold = json.dumps({"answer": c.expected["answer"], "evidence": c.expected["evidence"]}, ensure_ascii=False)
    v = h.validate(c, Response(content=gold), _prof())
    assert v.status == "OK" and v.sem == 1.0 and v.strict == 1.0


def test_h09_empty():
    import bench.tests.home_09 as h
    c = _h09_case()
    v = h.validate(c, Response(content=""), _prof())
    assert v.sem == 0.0 and v.status == "FORMAT_ERROR"


def test_h09_prose():
    import bench.tests.home_09 as h
    c = _h09_case()
    gold = json.dumps({"answer": c.expected["answer"], "evidence": c.expected["evidence"]}, ensure_ascii=False)
    v = h.validate(c, Response(content="Here is the answer: " + gold + " hope this helps"), _prof())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0 and v.strict == 0.0


def test_h09_wrong():
    import bench.tests.home_09 as h
    c = _h09_case()
    v = h.validate(c, Response(content=json.dumps({"answer": "Wrong Place XYZ", "evidence": c.expected["evidence"]})), _prof())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0


def test_h09_partial_evidence():
    import bench.tests.home_09 as h
    c = _h09_case()
    v = h.validate(c, Response(content=json.dumps({"answer": c.expected["answer"], "evidence": ["S001"]})), _prof())
    # Answer right -> OK (evidence only in details), sem stays 1.
    assert v.sem == 1.0 and v.details["evidence_f1"] < 1.0


# ---- HOME-10 ----
def _h10_case():
    import bench.tests.home_10 as h
    cases = h.load_cases(os.path.join(FIX, "HOME-10"))
    assert len(cases) == 3
    return cases[0]


def test_h10_gold():
    import bench.tests.home_10 as h
    c = _h10_case()
    v = h.validate(c, Response(content=json.dumps(c.expected, ensure_ascii=False)), _prof())
    assert v.status == "OK" and v.sem == 1.0


def test_h10_empty():
    import bench.tests.home_10 as h
    c = _h10_case()
    v = h.validate(c, Response(content=""), _prof())
    assert v.sem == 0.0 and v.status == "FORMAT_ERROR"


def test_h10_prose():
    import bench.tests.home_10 as h
    c = _h10_case()
    v = h.validate(c, Response(content="```json\n" + json.dumps(c.expected) + "\n```"), _prof())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0


def test_h10_wrong_partial():
    import bench.tests.home_10 as h
    c = _h10_case()
    bad = json.loads(json.dumps(c.expected))
    bad[0]["state"] = "lost" if bad[0]["state"] != "lost" else "ordered"
    v = h.validate(c, Response(content=json.dumps(bad)), _prof())
    assert v.status == "WRONG_ANSWER" and 0.0 < v.sem < 1.0


# ---- HOME-24 ----
def _h24_call_case():
    import bench.tests.home_24 as h
    cases = h.load_cases(os.path.join(FIX, "HOME-24"))
    c = next(x for x in cases if x.expected.get("expected_call") is not None)
    return c


def _h24_nocall_case():
    import bench.tests.home_24 as h
    cases = h.load_cases(os.path.join(FIX, "HOME-24"))
    return next(x for x in cases if x.expected.get("expected_call") is None)


def test_h24_gold():
    import bench.tests.home_24 as h
    c = _h24_call_case()
    exp = c.expected["expected_call"]
    v = h.validate(c, Response(content="", tool_calls=[{"name": exp["name"], "arguments": dict(exp["arguments"])}]), _prof())
    assert v.status == "OK" and v.sem == 1.0


def test_h24_empty_nocall_ok():
    import bench.tests.home_24 as h
    c = _h24_nocall_case()
    v = h.validate(c, Response(content="Paris"), _prof())
    assert v.status == "OK" and v.sem == 1.0


def test_h24_prose_textual():
    import bench.tests.home_24 as h
    c = _h24_call_case()
    exp = c.expected["expected_call"]
    txt = 'Sure: {"name": "%s", "arguments": %s}' % (exp["name"], json.dumps(exp["arguments"]))
    v = h.validate(c, Response(content=txt), _prof())
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0


def test_h24_wrong():
    import bench.tests.home_24 as h
    c = _h24_call_case()
    v = h.validate(c, Response(content="", tool_calls=[{"name": "get_weather", "arguments": {"city": "Nowhere", "unit": "celsius"}}]), _prof())
    # Either NO_CALL/BAD_CALL path; for a call case with wrong name it is WRONG_ANSWER.
    assert v.sem == 0.0 and v.status in ("WRONG_ANSWER", "FORMAT_ERROR")


def test_h24_unexpected_call():
    import bench.tests.home_24 as h
    c = _h24_nocall_case()
    v = h.validate(c, Response(content="", tool_calls=[{"name": "get_weather", "arguments": {"city": "Paris", "unit": "celsius"}}]), _prof())
    assert v.status == "WRONG_ANSWER" and v.sem == 0.0


# ---- HOME-18 ----
def _h18_cancel_case():
    import bench.tests.home_18 as h
    cases = h.load_cases(os.path.join(FIX, "HOME-18"))
    for c in cases:
        if (c.meta or {}).get("scenario") == "cancel_explicit":
            return c
    return cases[0]


def _chat_script(steps):
    # steps: list of ("call", name, args) or ("answer", text)
    state = {"i": 0}
    def fn(req: Request) -> Response:
        i = state["i"]
        state["i"] += 1
        if i < len(steps):
            kind = steps[i][0]
            if kind == "call":
                _, name, args = steps[i]
                return Response(content="", tool_calls=[{"name": name, "arguments": args}])
            else:
                return Response(content=steps[i][1])
        return Response(content='{"result": null}')
    return fn


def test_h18_gold():
    import bench.tests.home_18 as h
    c = _h18_cancel_case()
    exp_result = c.expected.get("result")
    fn = _chat_script([("call", "cancel_order", {"order_id": "ORD-1005"}),
                       ("answer", json.dumps({"result": exp_result}, ensure_ascii=False))])
    v, _ = h.run_case(c, _prof(), fn)
    assert v.sem == 1.0 and v.status == "OK", v.details


def test_h18_wrong_answer_state_only():
    import bench.tests.home_18 as h
    c = _h18_cancel_case()
    fn = _chat_script([("call", "cancel_order", {"order_id": "ORD-1005"}),
                       ("answer", json.dumps({"result": {"order_id": "WRONG"}}))])
    v, _ = h.run_case(c, _prof(), fn)
    assert v.sem == 0.5 and v.status == "WRONG_ANSWER"


def test_h18_textual_format():
    import bench.tests.home_18 as h
    c = _h18_cancel_case()
    exp_result = c.expected.get("result")
    fn = _chat_script([("answer", '{"name": "cancel_order", "arguments": {"order_id": "ORD-1005"}}'),
                       ("answer", json.dumps({"result": exp_result}))])
    v, _ = h.run_case(c, _prof(), fn)
    # Textual calls are executed (state ok) but flagged FORMAT_ERROR.
    assert v.details.get("textual") or v.status == "FORMAT_ERROR"


def test_h18_empty():
    import bench.tests.home_18 as h
    c = _h18_cancel_case()
    v, _ = h.run_case(c, _prof(), lambda req: Response(content=""))
    assert v.sem in (0.0, 0.5) and v.status == "FORMAT_ERROR"


# ---- HOME-21 ----
def _h21_case():
    import bench.tests.home_21 as h
    cases = h.load_cases(os.path.join(FIX, "HOME-21"))
    for c in cases:
        if (c.meta or {}).get("scenario") == "summarize_orders":
            return c
    return cases[0]


def test_h21_gold():
    import bench.tests.home_21 as h
    c = _h21_case()
    exp_result = c.expected.get("result")
    fn = _chat_script([("call", "get_order", {"order_id": "ORD-1001"}),
                       ("call", "get_order", {"order_id": "ORD-1002"}),
                       ("answer", json.dumps({"result": exp_result}, ensure_ascii=False))])
    v, _ = h.run_case(c, _prof(), fn)
    assert v.sem == 1.0 and v.status == "OK", v.details


def test_h21_prose_fence():
    import bench.tests.home_21 as h
    c = _h21_case()
    exp_result = c.expected.get("result")
    fn = _chat_script([("call", "get_order", {"order_id": "ORD-1001"}),
                       ("call", "get_order", {"order_id": "ORD-1002"}),
                       ("answer", "```json\n" + json.dumps({"result": exp_result}) + "\n```")])
    v, _ = h.run_case(c, _prof(), fn)
    assert v.status == "FORMAT_ERROR" and v.sem == 1.0


def test_h21_partial_wrong():
    import bench.tests.home_21 as h
    c = _h21_case()
    fn = _chat_script([("call", "get_order", {"order_id": "ORD-1001"}),
                       ("answer", json.dumps({"result": {"wrong": 1}}))])
    v, _ = h.run_case(c, _prof(), fn)
    assert v.sem in (0.0, 0.5) and v.status in ("WRONG_ANSWER", "FORMAT_ERROR")


# ---- HOME-02 / HOME-11 ----
def _embed_onehot(cases, corpus):
    ids = [p["id"] for p in corpus]
    idx = {d: i for i, d in enumerate(ids)}
    n = len(ids)
    primaries = []
    seconds = []
    for c in cases:
        qrels = c.expected.get("qrels", {})
        prim = next((d for d, g in qrels.items() if g == 2), next(iter(qrels)))
        sec = next((d for d, g in qrels.items() if g == 1), None)
        primaries.append(prim)
        seconds.append(sec)
    state = {"corpus_done": False, "qi": 0}
    def fn(texts):
        from bench.types import Response as R
        if not state["corpus_done"]:
            state["corpus_done"] = True
            embs = [[1.0 if j == i else 0.0 for j in range(n)] for i in range(n)]
            return R(content="", embeddings=embs)
        prim = primaries[state["qi"]]
        sec = seconds[state["qi"]]
        state["qi"] += 1
        vec = [0.0] * n
        vec[idx[prim]] = 1.0
        if sec is not None and sec in idx:
            vec[idx[sec]] = 0.5
        return R(content="", embeddings=[vec])
    return fn


def test_h02_gold_and_unsupported():
    import bench.tests.home_02 as h
    fx = os.path.join(FIX, "HOME-02")
    cases = h.load_cases(fx)
    assert len(cases) == 40
    corpus = h.load_corpus(fx)
    assert len(corpus) == 120
    prof = _prof(kind="embed")
    fn = _embed_onehot(cases[:2], corpus)
    out = h.run_embed(cases[:2], prof, fn)
    assert all(v.sem == 1.0 for _, v in out), [v.details for _, v in out]
    # Unsupported language: nomic-like profile with only English.
    prof2 = _prof(kind="embed")
    prof2.langs = ["en"]
    de_case = next(c for c in cases if c.input.get("query_lang") == "de")
    fn2 = _embed_onehot([de_case], corpus)
    out2 = h.run_embed([de_case], prof2, fn2)
    assert out2[0][1].status == "UNSUPPORTED_CAPABILITY"


def test_h02_empty_embedding():
    import bench.tests.home_02 as h
    fx = os.path.join(FIX, "HOME-02")
    cases = h.load_cases(fx)
    from bench.types import Response as R
    def bad(texts):
        return R(content="", embeddings=[[0.0] * 5 for _ in texts])
    prof = _prof(kind="embed")
    out = h.run_embed(cases[:1], prof, bad)
    # Zero vectors -> ranking arbitrary, sem in [0,1]; just check it runs.
    assert out[0][1].status in ("OK", "WRONG_ANSWER", "HARNESS_ERROR")


def test_h11_gold():
    import bench.tests.home_11 as h
    import bench.tests.home_02 as h02
    fx = os.path.join(FIX, "HOME-11")
    cases = h.load_cases(fx)
    assert len(cases) == 30
    corpus = h.load_corpus(fx)
    assert len(corpus) == 120
    prof = _prof(kind="embed")
    fn = _embed_onehot(cases[:2], corpus)
    out = h.run_embed(cases[:2], prof, fn)
    assert all(v.sem == 1.0 for _, v in out)
