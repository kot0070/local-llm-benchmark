"""FIX3 tests: /api/chat stop forwarding + HOME-23 repetition loop."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from bench import runner
from bench.ollama_client import OllamaClient
from bench.types import Case, Profile, Request, Response


def _plain():
    return Profile(tag="gemma3:12b", kind="chat", caps=["text", "vision"], think="none",
                   ctx_max=131072, sampling={}, adapters={})


class _Rec:
    last_body = None


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            _Rec.last_body = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            _Rec.last_body = {}
        chunks = [
            {"model": "m", "message": {"role": "assistant", "content": "hi"}, "done": False},
            {"model": "m", "message": {"role": "assistant", "content": ""}, "done": True,
             "done_reason": "stop", "prompt_eval_count": 1, "eval_count": 1,
             "load_duration": 1000, "prompt_eval_duration": 1000, "eval_duration": 1000},
        ]
        body = "".join(json.dumps(c) + "\n" for c in chunks).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _client():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, OllamaClient(url=f"http://127.0.0.1:{srv.server_address[1]}")


def test_chat_sends_stop_in_options():
    srv, c = _client()
    try:
        opts = {"temperature": 0.0}
        c.chat("m", [{"role": "user", "content": "hi"}], opts, stop=["X"], timeout=20.0)
        assert _Rec.last_body["options"]["stop"] == ["X"]
        assert opts == {"temperature": 0.0}  # caller dict not mutated
        c.chat("m", [{"role": "user", "content": "hi"}], {"temperature": 0.0}, timeout=20.0)
        assert "stop" not in (_Rec.last_body.get("options") or {})
    finally:
        srv.shutdown()


def test_runner_chat_forwards_stop():
    import time
    from types import SimpleNamespace

    seen = {}

    class FakeClient:
        def chat(self, model, messages, options, think=None, tools=None, fmt=None,
                 timeout=60.0, stop=None):
            seen["stop"] = stop
            seen["options"] = dict(options)
            return Response(content="ok", done_reason="stop")

    profile = Profile(tag="glm-ocr:latest", kind="chat", caps=["vision"], think="none",
                      ctx_max=131072, sampling={"default": {"temperature": 0.0}},
                      adapters={}, stop=[], profile_id="p")
    ctx = SimpleNamespace(client=FakeClient(), deadline=time.time() + 60,
                          current_case_id="HOME-23-01")
    meta = {"version": "n1", "mode": "R0", "num_predict": 1024, "think_extra": 0,
            "num_ctx": 12288, "timeout_s": 180, "family": "OCR"}
    req = Request(endpoint="chat", messages=[{"role": "user", "content": "Text Recognition:"}],
                  options={"stop": ["\n```"]})
    runner.do_request(ctx, profile, meta, req, False, 60.0, [])
    assert seen["stop"] and "\n```" in seen["stop"]
    # tools_loop chat_fn path forwards stop as well
    seen.clear()
    fn = runner.make_chat_fn(ctx, profile, meta, False, [])
    fn(Request(endpoint="chat", messages=[{"role": "user", "content": "x"}],
               options={"stop": ["\n```"]}))
    assert seen["stop"] and "\n```" in seen["stop"]


def _text_case(text):
    return Case(id="HOME-23-01", test_id="HOME-23", tier="easy", lang="en",
                input={"mode": "text"}, expected={"text": text}, meta={"mode": "text"})


def test_home23_gold_ok():
    from bench.tests import home_23 as m
    gold = "The harbor warehouse received forty-two crates of copper wire."
    v = m.validate(_text_case(gold), Response(content=gold), _plain())
    assert v.status == "OK" and v.sem == 1.0


def test_home23_repetition_loop_flagged():
    from bench.tests import home_23 as m
    gold = "The harbor warehouse received forty-two crates of copper wire."
    hyp = f"{gold}\n```\n{gold}\n```markdown\n{gold}"
    v = m.validate(_text_case(gold), Response(content=hyp), _plain())
    assert v.status == "FORMAT_ERROR"
    assert v.details.get("sub_reason") == "REPETITION_LOOP"
    assert v.sem == 1.0 and v.strict == 0.0
    assert int(v.details.get("dedup_removed_blocks", 0)) >= 1


def test_home23_wrong_still_wrong():
    from bench.tests import home_23 as m
    gold = "The harbor warehouse received forty-two crates of copper wire."
    v = m.validate(_text_case(gold), Response(content="completely unrelated zzzqqq 12345"), _plain())
    assert v.status == "WRONG_ANSWER"


def _table_case():
    rows = [["Item", "Qty", "Price"], ["Bolts M12", "40", "1.20"], ["Nails", "5", "0.10"]]
    return (Case(id="HOME-23-11", test_id="HOME-23", tier="easy", lang="en",
                 input={"mode": "table"}, expected={"rows": rows}, meta={"mode": "table"}), rows)


def _html(rows):
    return "<table>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</table>"


def test_home23_table_dup_rows_flagged():
    from bench.tests import home_23 as m
    case, rows = _table_case()
    dup = rows + rows  # whole-block repeat inside one table
    v = m.validate(case, Response(content=_html(dup)), _plain())
    assert v.status == "FORMAT_ERROR"
    assert v.details.get("sub_reason") == "REPETITION_LOOP"
    assert v.sem == 1.0 and v.strict == 0.0
