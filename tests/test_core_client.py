"""Core client tests against the mock Ollama server."""
import os

import pytest

from bench.ollama_client import OllamaClient, OllamaError
from tests.mock_ollama import start

_port = None
_srv = None


def client():
    global _port, _srv
    if _srv is None:
        _srv, _port = start(0)
    os.environ["BENCH_OLLAMA_URL"] = f"http://127.0.0.1:{_port}"
    return OllamaClient()


def test_chat_echo_and_counts():
    c = client()
    r = c.chat("mock-chat:latest", [{"role": "user", "content": "hello world"}],
               {"temperature": 0.0}, think=False, timeout=20.0)
    assert "reply:hello world" in r.content
    assert r.done_reason == "stop"
    assert r.eval_count and r.eval_count >= 1
    assert r.prompt_eval_count == 10
    assert r.ttft_s is not None and r.ttft_s >= 0
    assert r.wall_s > 0
    assert r.http_status == 200


def test_generate_thinking_split():
    c = client()
    r = c.generate("mock-chat:latest", "THINK puzzle", {"num_ctx": 4096},
                   timeout=20.0)
    assert r.thinking == "step one, step two"
    assert "thoughtful answer" in r.content


def test_generate_think_leak_visible_to_runner():
    c = client()
    r = c.generate("mock-chat:latest", "THINK_LEAK please", {"num_ctx": 4096},
                   timeout=20.0)
    assert "<think>leaked thought</think>" in r.content


def test_trunc_done_reason():
    c = client()
    r = c.generate("mock-chat:latest", "TRUNC long", {"num_ctx": 4096},
                   timeout=20.0)
    assert r.done_reason == "length"
    assert "partial answer" in r.content


def test_tool_calls_native():
    c = client()
    r = c.chat("mock-chat:latest", [{"role": "user", "content": "TOOL weather?"}],
               {}, think=False, timeout=20.0)
    assert r.tool_calls, "expected native tool_calls from mock"
    assert r.tool_calls[0]["function"]["name"] == "get_weather"


def test_ctx_overflow_400():
    c = client()
    with pytest.raises(OllamaError) as e:
        c.generate("mock-chat:latest", "CTX_OVERFLOW " + "x" * 100,
                   {"num_ctx": 4096}, timeout=20.0)
    assert e.value.http_status == 400
    assert "exceed" in e.value.body.lower()


def test_http500():
    c = client()
    with pytest.raises(OllamaError) as e:
        c.chat("mock-chat:latest", [{"role": "user", "content": "HTTP500 boom"}],
               {}, timeout=20.0)
    assert e.value.http_status == 500


def test_timeout_slow_reply():
    c = client()
    with pytest.raises(TimeoutError):
        c.chat("mock-chat:latest", [{"role": "user", "content": "SLOW please"}],
               {}, timeout=1.0)


def test_embed_vectors():
    c = client()
    r = c.embed("mock-embed:latest", ["hello", "world"], timeout=20.0)
    assert len(r.embeddings) == 2
    assert len(r.embeddings[0]) == 16
    r2 = c.embed("mock-embed:latest", ["hello"], timeout=20.0)
    assert r2.embeddings[0] == r.embeddings[0]


def test_version_tags_show_ps():
    c = client()
    assert c.version() == "0.34.2-mock"
    tags = c.tags()
    assert any(t["name"] == "mock-chat:latest" for t in tags)
    assert c.show("mock-chat:latest")["template"] == "mock-template"
    ps = c.ps()
    assert "models" in ps
    # mock tracks loaded models with size/size_vram for offload tests;
    # unload everything then ps must be empty again
    for m in list(ps.get("models", [])):
        c.unload(m.get("name") or m.get("model", ""))
    assert c.ps()["models"] == []
    # reload one model -> ps exposes size/size_vram/offload fields
    c.chat("mock-chat:latest", [{"role": "user", "content": "hi"}],
           {"temperature": 0.0}, timeout=20.0)
    ps2 = c.ps()
    assert ps2["models"], "expected loaded entry after chat"
    entry = ps2["models"][0]
    assert entry["size"] > 0 and entry["size_vram"] > 0
    assert 0.0 < entry["size_vram"] / entry["size"] <= 1.0
    c.unload("mock-chat:latest")
