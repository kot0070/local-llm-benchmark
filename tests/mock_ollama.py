"""Threaded mock Ollama server for core tests. Stdlib only.

Endpoints: /api/version, /api/tags, /api/show, /api/ps, /api/chat,
/api/generate (streaming NDJSON, scripted replies), /api/embed.

Scripting (matched against model name + prompt/messages text):
- "SLOW" -> sleep 6 s (drives client timeouts)
- "CTX_OVERFLOW" -> HTTP 400 {"error": "model context exceed ..."}
- "OOM_GPU" -> HTTP 500 {"error": "CUDA error: out of memory"}
- "HTTP500" -> HTTP 500 {"error": "internal server error boom"}
- "THINK_LEAK" -> content "<think>leaked thought</think>final answer", empty thinking
- "TRUNC" -> done_reason "length" with partial content
- "TOOL" -> chat tool_calls [{"function": {"name": "get_weather", ...}}]
- default echo: content "reply:" + first 60 chars of prompt
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODELS = [
    {"name": "mock-chat:latest", "digest": "sha256:aaa111",
     "size": 1000, "capabilities": ["completion"]},
    {"name": "mock-embed:latest", "digest": "sha256:bbb222",
     "size": 500, "capabilities": ["embed"]},
    {"name": "mock-tools:latest", "digest": "sha256:ccc333",
     "size": 1000, "capabilities": ["completion", "tools"]},
]


def _prompt_of(obj: dict) -> str:
    parts = [str(obj.get("model", "")), str(obj.get("prompt", ""))]
    for m in obj.get("messages", []) or []:
        parts.append(str(m.get("content", "")))
    return "\n".join(parts)


def _ndjson_chat(reply: str, thinking: str = "", tool_calls: list | None = None,
                 done_reason: str = "stop", trunks: int = 2) -> list[dict]:
    chunks = []
    n = max(1, trunks)
    for i in range(n):
        piece = reply[i * len(reply) // n:(i + 1) * len(reply) // n]
        msg: dict = {"role": "assistant", "content": piece}
        if i == 0 and thinking:
            msg["thinking"] = thinking
        if i == 0 and tool_calls:
            msg["tool_calls"] = tool_calls
        chunks.append({"model": "mock", "created_at": "t",
                       "message": msg, "done": False})
    chunks.append({"model": "mock", "created_at": "t",
                   "message": {"role": "assistant", "content": ""},
                   "done": True, "done_reason": done_reason,
                   "prompt_eval_count": 10, "eval_count": max(1, len(reply.split())),
                   "load_duration": 5_000_000, "prompt_eval_duration": 10_000_000,
                   "eval_duration": 50_000_000})
    return chunks


def _ndjson_generate(reply: str, thinking: str = "",
                     done_reason: str = "stop") -> list[dict]:
    half = len(reply) // 2
    return [
        {"model": "mock", "response": reply[:half], "thinking": thinking,
         "done": False},
        {"model": "mock", "response": reply[half:], "done": True,
         "done_reason": done_reason, "prompt_eval_count": 10,
         "eval_count": max(1, len(reply.split())),
         "load_duration": 5_000_000, "prompt_eval_duration": 10_000_000,
         "eval_duration": 50_000_000},
    ]


def scripted(obj: dict, is_embed: bool = False):
    """Return (http_status, payload_obj_or_chunks, stream: bool)."""
    text = _prompt_of(obj)
    if "SLOW" in text:
        time.sleep(6.0)
        return 200, _ndjson_chat("slow reply done"), True
    if "CTX_OVERFLOW" in text:
        return 400, {"error": "model context exceed: prompt too long"}, False
    if "OOM_GPU" in text:
        return 500, {"error": "CUDA error: out of memory"}, False
    if "HTTP500" in text:
        return 500, {"error": "internal server error boom"}, False
    model = str(obj.get("model", ""))
    if is_embed or "embed" in model:
        inputs = obj.get("input", obj.get("inputs", []))
        if isinstance(inputs, str):
            inputs = [inputs]
        vecs = []
        for t in inputs:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            vecs.append([((b / 255.0) - 0.5) for b in h[:16]])
        return 200, {"model": model, "embeddings": vecs}, False
    if "THINK_LEAK" in text:
        chunks = _ndjson_chat("<think>leaked thought</think>final answer")
        return 200, chunks, True
    if "TRUNC" in text:
        chunks = _ndjson_chat("partial answer that was cut", done_reason="length")
        return 200, chunks, True
    if "TOOL" in text:
        tc = [{"function": {"name": "get_weather",
                            "arguments": {"city": "Paris", "unit": "c"}}}]
        chunks = _ndjson_chat("calling weather tool", tool_calls=tc)
        return 200, chunks, True
    if "THINK" in text:
        chunks = _ndjson_chat("thoughtful answer", thinking="step one, step two")
        return 200, chunks, True
    prompt = str(obj.get("prompt", "")) or " ".join(
        str(m.get("content", "")) for m in obj.get("messages", []) or [])
    return 200, _ndjson_chat("reply:" + prompt[:60]), True


class Handler(BaseHTTPRequestHandler):
    server_version = "MockOllama/1"
    # last loaded model per server instance (for /api/ps offload simulation)
    loaded: dict = {}

    def log_message(self, *a):
        pass

    def _send(self, status: int, obj, stream: bool = False):
        if stream:
            body = "".join(json.dumps(c) + "\n" for c in obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            # write in two parts to exercise streaming clients
            half = len(body) // 2
            self.wfile.write(body[:half])
            self.wfile.flush()
            time.sleep(0.01)
            self.wfile.write(body[half:])
        else:
            body = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        if self.path == "/api/version":
            self._send(200, {"version": "0.34.2-mock"})
        elif self.path == "/api/tags":
            self._send(200, {"models": MODELS})
        elif self.path == "/api/ps":
            loaded = getattr(self.server, "mock_loaded", {})
            models = []
            for name, entry in loaded.items():
                size = entry.get("size", 1000)
                models.append({"name": name, "model": name,
                               "size": size,
                               "size_vram": int(size * 0.8),
                               "context_length": 4096,
                               "details": {}})
            self._send(200, {"models": models})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        obj = self._read_json()
        if self.path == "/api/show":
            self._send(200, {"template": "mock-template",
                             "parameters": "temperature 0.0",
                             "capabilities": ["completion"]})
        elif self.path == "/api/chat":
            _track_load(self.server, obj)
            st, payload, stream = scripted(obj)
            self._send(st, payload, stream)
        elif self.path == "/api/generate":
            # unload request: keep_alive 0 clears the loaded entry
            try:
                if obj.get("keep_alive") == 0 and obj.get("model"):
                    loaded = getattr(self.server, "mock_loaded", {})
                    loaded.pop(str(obj.get("model")), None)
                    self.server.mock_loaded = loaded
                    st, payload, stream = scripted(obj)
                    self._send(st, payload, stream)
                    return
            except Exception:
                pass
            _track_load(self.server, obj)
            st, payload, stream = scripted(obj)
            self._send(st, payload, stream)
        elif self.path == "/api/embed":
            _track_load(self.server, obj)
            st, payload, stream = scripted(obj, is_embed=True)
            self._send(st, payload, stream)
        else:
            self._send(404, {"error": "not found"})


def _track_load(server, obj: dict) -> None:
    try:
        name = str(obj.get("model") or "")
        if not name:
            return
        size = 1000
        for m in MODELS:
            if m.get("name") == name:
                size = int(m.get("size", 1000))
                break
        loaded = getattr(server, "mock_loaded", {})
        loaded[name] = {"size": size}
        server.mock_loaded = loaded
    except Exception:
        pass


def start(port: int = 0) -> tuple[ThreadingHTTPServer, int]:
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


if __name__ == "__main__":
    srv, port = start(11499)
    print(f"mock ollama on 127.0.0.1:{port}")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
