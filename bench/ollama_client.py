"""Minimal Ollama HTTP client (urllib, stream=true NDJSON). No third-party deps."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from bench.types import Response

DEFAULT_URL = "http://127.0.0.1:11434"


class OllamaError(Exception):
    def __init__(self, message: str, http_status: int | None = None, body: str = ""):
        super().__init__(message)
        self.http_status = http_status
        self.body = body


def base_url() -> str:
    import os
    return os.environ.get("BENCH_OLLAMA_URL", DEFAULT_URL)


def _post_json(url: str, payload: dict, timeout: float) -> tuple[int, list[str]]:
    """POST JSON, return (http_status, raw_lines). Raises OllamaError/TimeoutError."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, raw.splitlines()
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise OllamaError(f"HTTP {e.code}: {body[:500]}", http_status=e.code, body=body)
    except TimeoutError:
        raise
    except Exception as e:
        if "timed out" in str(e).lower() or "timeout" in type(e).__name__.lower():
            raise TimeoutError(str(e))
        raise OllamaError(f"connection error: {e}")


def _parse_chat_stream(lines: list[str], wall_s: float, t_first: float | None) -> Response:
    content_parts: list[str] = []
    thinking_parts: list[str] = []
    tool_calls: list = []
    done_reason = None
    prompt_eval_count = eval_count = None
    load_s = prompt_eval_s = eval_s = None
    raw_last: dict = {}
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError:
            continue
        raw_last = obj
        msg = obj.get("message") or {}
        c = msg.get("content") or obj.get("response") or ""
        t = msg.get("thinking") or obj.get("thinking") or ""
        if c:
            content_parts.append(c)
        if t:
            thinking_parts.append(t)
        tc = msg.get("tool_calls") or obj.get("tool_calls") or []
        if tc:
            tool_calls.extend(tc)
        if obj.get("done"):
            done_reason = obj.get("done_reason") or obj.get("done_reason_final")
            prompt_eval_count = obj.get("prompt_eval_count")
            eval_count = obj.get("eval_count")
            for k_src, k_dst in (("load_duration", "load"), ("prompt_eval_duration", "pe"),
                                 ("eval_duration", "ev")):
                v = obj.get(k_src)
                if isinstance(v, (int, float)):
                    if k_dst == "load":
                        load_s = v / 1e9
                    elif k_dst == "pe":
                        prompt_eval_s = v / 1e9
                    else:
                        eval_s = v / 1e9
    ttft = (t_first - (time.time() - wall_s)) if t_first is not None else None
    return Response(content="".join(content_parts), thinking="".join(thinking_parts),
                    tool_calls=tool_calls, done_reason=done_reason,
                    prompt_eval_count=prompt_eval_count, eval_count=eval_count,
                    load_s=load_s, prompt_eval_s=prompt_eval_s, eval_s=eval_s,
                    ttft_s=ttft, wall_s=wall_s, raw=raw_last)


class OllamaClient:
    def __init__(self, url: str | None = None, timeout: float = 120.0):
        self.url = (url or base_url()).rstrip("/")

    # -- low level -----------------------------------------------------
    def _stream(self, endpoint: str, payload: dict, timeout: float) -> Response:
        payload = dict(payload)
        payload["stream"] = True
        t0 = time.time()
        status, lines = _post_json(self.url + endpoint, payload, timeout)
        wall = time.time() - t0
        void = status  # 2xx guaranteed (HTTPError raised otherwise)
        resp = self._parse_lines(lines, wall, t0)
        resp.http_status = status
        return resp

    @staticmethod
    def _parse_lines(lines: list[str], wall: float, t0: float) -> Response:
        # t_first_token approximated: streaming chunk times unavailable after
        # full read, so ttft is left None here and set by callers that stream.
        return _parse_chat_stream(lines, wall, None)

    def _stream_timed(self, endpoint: str, payload: dict, timeout: float) -> Response:
        """POST with per-chunk timing so ttft_s reflects first-token latency."""
        import http.client
        import urllib.parse
        payload = dict(payload)
        payload["stream"] = True
        body = json.dumps(payload).encode("utf-8")
        u = urllib.parse.urlparse(self.url)
        t0 = time.time()
        t_first = None
        buf_lines: list[str] = []
        try:
            if u.scheme == "https":
                conn = http.client.HTTPSConnection(u.hostname, u.port or 443, timeout=timeout)
            else:
                conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)
            conn.request("POST", endpoint, body=body,
                         headers={"Content-Type": "application/json"})
            r = conn.getresponse()
            status = r.status
            if status >= 400:
                raw = r.read().decode("utf-8", errors="replace")
                conn.close()
                raise OllamaError(f"HTTP {status}: {raw[:500]}", http_status=status, body=raw)
            chunks: list[bytes] = []
            while True:
                part = r.read1(65536)  # read() on a chunked body blocks until 64 KB: ttft would be ~wall
                if not part:
                    break
                if t_first is None:
                    t_first = time.time()
                chunks.append(part)
            conn.close()
        except OllamaError:
            raise
        except Exception as e:
            if "timed out" in str(e).lower() or "timeout" in type(e).__name__.lower():
                raise TimeoutError(str(e))
            raise OllamaError(f"connection error: {e}")
        wall = time.time() - t0
        text = b"".join(chunks).decode("utf-8", errors="replace")
        resp = _parse_chat_stream(text.splitlines(), wall, t_first if t_first else None)
        if t_first is not None:
            resp.ttft_s = t_first - t0
        resp.http_status = status
        return resp

    # -- public API ----------------------------------------------------
    def chat(self, model: str, messages: list, options: dict, think=None,
             tools: list | None = None, fmt=None, keep_alive: str = "30m",
             timeout: float = 120.0, stop: list | None = None) -> Response:
        payload: dict = {"model": model, "messages": messages, "options": dict(options),
                         "truncate": False, "keep_alive": keep_alive}
        if stop:
            payload["options"]["stop"] = stop
        if think is not None:
            payload["think"] = think
        if tools:
            # Ollama expects [{"type": "function", "function": {...}}]; wrap flat {"name", "parameters"} tool dicts.
            payload["tools"] = [t if (isinstance(t, dict) and t.get("type") == "function" and "function" in t)
                                else {"type": "function", "function": t} for t in tools]
        if fmt is not None:
            payload["format"] = fmt
        # drop empty options keys that Ollama would reject? keep explicit.
        return self._stream_timed("/api/chat", payload, timeout)

    def generate(self, model: str, prompt: str, options: dict, raw: bool = False,
                 stop: list | None = None, think=None, keep_alive: str = "30m",
                 timeout: float = 120.0) -> Response:
        payload: dict = {"model": model, "prompt": prompt, "options": dict(options),
                         "truncate": False, "keep_alive": keep_alive}
        if raw:
            payload["raw"] = True
        if stop:
            payload["options"]["stop"] = stop
        if think is not None and not raw:
            payload["think"] = think
        return self._stream_timed("/api/generate", payload, timeout)

    def embed(self, model: str, inputs: list[str], keep_alive: str = "30m",
              timeout: float = 120.0) -> Response:
        payload = {"model": model, "input": inputs, "truncate": False,
                   "keep_alive": keep_alive}
        t0 = time.time()
        try:
            _status, lines = _post_json(self.url + "/api/embed", payload, timeout)
        except Exception:
            raise
        wall = time.time() - t0
        obj: dict = {}
        for ln in lines:
            ln = ln.strip()
            if ln:
                try:
                    obj = json.loads(ln)
                    break
                except json.JSONDecodeError:
                    continue
        return Response(wall_s=wall, http_status=200, raw=obj,
                        embeddings=obj.get("embeddings"))

    def _get(self, path: str, timeout: float = 30.0) -> dict:
        req = urllib.request.Request(self.url + path, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
        except urllib.error.HTTPError as e:
            raise OllamaError(f"HTTP {e.code} on {path}", http_status=e.code)
        except Exception as e:
            if "timed out" in str(e).lower():
                raise TimeoutError(str(e))
            raise OllamaError(f"connection error on {path}: {e}")

    def version(self) -> str:
        try:
            return str(self._get("/api/version").get("version", "unknown"))
        except OllamaError:
            return "unknown"

    def tags(self) -> list[dict]:
        try:
            return self._get("/api/tags").get("models", [])
        except OllamaError:
            return []

    def show(self, model: str) -> dict:
        data = json.dumps({"model": model}).encode("utf-8")
        req = urllib.request.Request(self.url + "/api/show", data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
        except Exception as e:
            raise OllamaError(f"show failed for {model}: {e}")

    def ps(self) -> dict:
        try:
            return self._get("/api/ps")
        except OllamaError as e:
            return {"models": [], "_error": str(e)}

    def unload(self, model: str, timeout: float = 60.0) -> None:
        payload = {"model": model, "keep_alive": 0, "prompt": "",
                   "options": {"num_ctx": 4096}}
        try:
            _post_json(self.url + "/api/generate", payload, timeout)
        except OllamaError:
            pass
