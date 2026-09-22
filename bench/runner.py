"""NIGHT-1 runner: planner + scheduler + time budget + status precedence.

Usage: python -m bench.runner --budget-hours 8 [--run-id X | --resume X]
       [--models tag,...] [--tests HOME-..,...] [--smoke]
       [--phase {all,1,2,3}] [--dry-run]
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import os
import re
import sys
import time
import traceback
import zlib

from bench import env as envmod
from bench import registry as registrymod
from bench import store as storemod
from bench.ollama_client import OllamaClient, OllamaError, base_url
from bench.types import (Case, Profile, Request, Response, Verdict,
                         MODEL_OUTCOME, RETRYABLE)

THINK_RE = re.compile(r"\A\s*<think>(.*?)</think>\s*", re.DOTALL | re.IGNORECASE)
OOM_RAM_RE = re.compile(r"\bram\b")

# ---------------------------------------------------------------- profiles

def load_profiles(path: str | None = None) -> dict[str, Profile]:
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__))
                            if os.path.basename(os.path.dirname(__file__)) == "bench"
                            else os.getcwd(), "config", "profiles.json")
        # bench/runner.py -> project root is parent of bench/
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                            "config", "profiles.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out: dict[str, Profile] = {}
    for tag, p in raw["profiles"].items():
        out[tag] = Profile(tag=tag, kind=p.get("kind", "chat"),
                           caps=p.get("caps", []), think=p.get("think", "none"),
                           ctx_max=p.get("ctx_max", 4096),
                           sampling=p.get("sampling", {}),
                           adapters=p.get("adapters", {}),
                           stop=p.get("stop", []),
                           system=p.get("system"),
                           embed_prefix=p.get("embed_prefix", {}),
                           profile_id=p.get("profile_id", ""),
                           notes=p.get("notes", ""),
                           langs=p.get("langs", ["multi"]))
    return out


def load_eligibility(path: str | None = None) -> dict:
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                            "config", "eligibility_night.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- think/options

def resolve_think(profile: Profile, mode: str) -> tuple[bool | None, list[str]]:
    """Return (think_value_or_None, flags). None means: do not send think."""
    flags: list[str] = []
    if profile.think == "none":
        return None, flags
    if profile.think == "toggle":
        return (mode == "R1"), flags
    if profile.think == "always":
        if mode == "R0":
            flags.append("THINKING_FORCED")
        return True, flags
    return None, flags


def resolve_options(profile: Profile, meta: dict, request: Request,
                    think: bool | None, num_predict: int, num_ctx: int,
                    seed: int) -> tuple[dict, list]:
    sampling = profile.sampling or {}
    if think and meta.get("family") == "CODE" and "thinking_code" in sampling:
        base = sampling["thinking_code"]
    elif think and "thinking" in sampling:
        base = sampling["thinking"]
    elif not think and "nonthinking" in sampling:
        base = sampling["nonthinking"]
    else:
        base = sampling.get("default", {})
    options = dict(base)
    for k, v in (request.options or {}).items():
        if k == "stop":
            continue
        options[k] = v
    options["num_predict"] = num_predict
    options["num_ctx"] = num_ctx
    options["seed"] = seed
    stop = list(profile.stop or [])
    extra = (request.options or {}).get("stop", [])
    if extra:
        stop = stop + list(extra)
    return options, stop


def num_predict_for(meta: dict, think: bool | None) -> int:
    base = int(meta.get("num_predict", 256) or 256)
    if think:
        base += int(meta.get("think_extra", 0) or 0)
    return base


def apply_system(profile: Profile, request: Request) -> Request:
    if (profile.system and request.endpoint in ("chat",) and request.messages):
        if not any(m.get("role") == "system" for m in request.messages):
            msgs = [{"role": "system", "content": profile.system}] + list(request.messages)
            return Request(endpoint=request.endpoint, messages=msgs,
                           prompt=request.prompt, raw=request.raw, tools=request.tools,
                           format=request.format, think=request.think,
                           options=request.options, embed_input=request.embed_input,
                           force_think=request.force_think)
    return request


# ---------------------------------------------------------------- errors

def classify_exception(exc: BaseException, during_load: bool = False) -> tuple[str, str, str]:
    """Map transport errors to (status, sub_reason, attribution)."""
    if isinstance(exc, TimeoutError):
        return "TIMEOUT", "REQUEST_TIMEOUT", "RUNTIME"
    if isinstance(exc, OllamaError):
        body = (exc.body or "") + " " + str(exc)
        low = body.lower()
        if exc.http_status == 400 and ("exceed" in low or "context" in low):
            return "CONTEXT_OVERFLOW", "PROMPT_TOO_LONG", "RUNTIME"
        if ("cuda error: out of memory" in low or "out of memory" in low
                or "failed to allocate" in low or "not enough memory" in low
                or "insufficient memory" in low):
            if ("system memory" in low or "host memory" in low
                    or "cpu buffer" in low or "not enough memory" in low
                    or "insufficient memory" in low
                    or OOM_RAM_RE.search(low)):
                return "OOM_RAM", "ALLOC_FAILED", "ENVIRONMENT"
            return "OOM_GPU", "ALLOC_FAILED", "ENVIRONMENT"
        if during_load:
            return "MODEL_LOAD_ERROR", f"HTTP_{exc.http_status or 'ERR'}", "RUNTIME"
        return "MODEL_RUNTIME_ERROR", f"HTTP_{exc.http_status or 'ERR'}", "RUNTIME"
    return "HARNESS_ERROR", f"{type(exc).__name__}: {exc}"[:200], "HARNESS"


def strip_think_leak(content: str, thinking: str) -> tuple[str, str, bool]:
    m = THINK_RE.match(content or "")
    if m:
        leaked = m.group(1)
        rest = content[m.end():]
        combined = (thinking + "\n" + leaked).strip() if thinking else leaked
        return rest, combined, True
    return content, thinking, False


# ---------------------------------------------------------------- sizes

def model_size_gb(tag: str) -> float:
    m = re.search(r":(\d+(?:\.\d+)?)([mb])\b", tag.lower())
    if not m:
        m = re.search(r"(\d+(?:\.\d+)?)([mb])\b", tag.lower())
    if not m:
        return float("inf")
    val = float(m.group(1))
    return val if m.group(2) == "b" else val / 1000.0


def fetch_size_map(client) -> dict[str, int]:
    """Return {tag: size_bytes} from /api/tags. Missing -> {} (fallback to tag parse)."""
    try:
        tags = client.tags()
    except Exception:
        return {}
    out: dict[str, int] = {}
    for t in tags or []:
        name = t.get("name", "")
        size = t.get("size")
        if name and isinstance(size, (int, float)) and size > 0:
            out[name] = int(size)
    return out


def sort_by_actual_size(tags: list[str], size_by_tag: dict | None) -> list[str]:
    """Sort ascending by actual size bytes; unknown sizes last, then tag parse, then name."""
    size_by_tag = size_by_tag or {}

    def key(t: str):
        if t in size_by_tag:
            return (0, size_by_tag[t], t)
        # fallback to tag-parse estimate when /api/tags has no entry
        est = model_size_gb(t)
        if est != float("inf"):
            return (1, est, t)
        return (2, float("inf"), t)
    return sorted(tags, key=key)


# ---------------------------------------------------------------- runner ctx

class Ctx:
    def __init__(self, args, run_dir: str, modules: dict, profiles: dict,
                 elig: dict, client: OllamaClient, store: storemod.Store,
                 deadline: float, ollama_version: str = "unknown",
                 digest_by_tag: dict | None = None,
                 show_by_tag: dict | None = None):
        self.args = args
        self.run_dir = run_dir
        self.modules = modules
        self.profiles = profiles
        self.elig = elig
        self.client = client
        self.store = store
        self.deadline = deadline
        self.ollama_version = ollama_version
        self.digest_by_tag = digest_by_tag or {}
        self.show_by_tag = show_by_tag or {}
        self.speeds: dict[str, dict] = {}  # tag -> {gen_tok_s, prompt_tok_s}
        self.unload_failed_tags: set[str] = set()
        self.load_info: dict[str, dict] = {}  # tag -> {size, size_vram, ...}
        self.size_by_tag: dict[str, int] = {}
        self.baseline: dict = {}
        self.monitor = None  # env.Monitor, set in main
        self.server_log_path = os.path.expandvars(r"%LOCALAPPDATA%\Ollama\server.log")
        self.server_log_offset = 0
        try:
            if os.path.exists(self.server_log_path):
                self.server_log_offset = os.path.getsize(self.server_log_path)
        except OSError:
            pass


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def local_now() -> str:
    return datetime.datetime.now().astimezone().isoformat()


def prompt_sha(request: Request) -> str:
    if request.endpoint == "generate":
        return hashlib.sha256((request.prompt or "").encode("utf-8")).hexdigest()
    return hashlib.sha256(json.dumps(request.messages or [],
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def identity_for(ctx: Ctx, tag: str) -> dict:
    digest = getattr(ctx, "digest_by_tag", {}).get(tag, "unknown")
    show = getattr(ctx, "show_by_tag", {}).get(tag, {})
    template = show.get("template", "") if isinstance(show, dict) else ""
    params = show.get("parameters", "") if isinstance(show, dict) else ""
    caps = show.get("capabilities", []) if isinstance(show, dict) else []
    return {"tag": tag, "digest": digest,
            "template_sha256": hashlib.sha256(str(template).encode("utf-8")).hexdigest(),
            "params_sha256": hashlib.sha256(str(params).encode("utf-8")).hexdigest(),
            "capabilities": caps, "ollama_version": ctx.ollama_version}


def server_log_slice(ctx: Ctx, max_chars: int = 4000) -> str:
    try:
        if not os.path.exists(ctx.server_log_path):
            return ""
        with open(ctx.server_log_path, "rb") as f:
            f.seek(ctx.server_log_offset)
            data = f.read(256 * 1024).decode("utf-8", errors="replace")
        lines = [ln for ln in data.splitlines()
                 if any(k in ln.lower() for k in ("offloaded", "using device", "n_ctx",
                                                  "flash_attn", "error", "load"))]
        return "\n".join(lines)[-max_chars:]
    except Exception:
        return ""


OFFLOAD_LAYERS_RE = re.compile(r"offloaded\s+(\d+)\s*/\s*(\d+)\s*layers?",
                               re.IGNORECASE)


def parse_offload_layers(text: str) -> tuple[int | None, int | None]:
    """Parse 'offloaded N/M layers' from a server.log slice."""
    if not text:
        return None, None
    last = None
    for m in OFFLOAD_LAYERS_RE.finditer(text):
        try:
            last = (int(m.group(1)), int(m.group(2)))
        except ValueError:
            continue
    if last is None:
        return None, None
    return last


def capture_load_info(ctx: Ctx, tag: str) -> dict:
    """Call /api/ps after a model load; store size/size_vram/offload/context/layers.

    Updates ctx.load_info[tag] and returns it. Never raises.
    """
    info: dict = {"size": None, "size_vram": None, "offload_ratio": None,
                  "context_length": None, "layers_gpu": None,
                  "layers_total": None}
    try:
        ps = ctx.client.ps()
        models = (ps or {}).get("models", []) or []
        entry = None
        for m in models:
            name = str(m.get("name") or m.get("model") or "")
            if name == tag:
                entry = m
                break
        if entry is None:
            for m in models:
                name = str(m.get("name") or m.get("model") or "")
                if name and (tag in name or name in tag):
                    entry = m
                    break
        if isinstance(entry, dict):
            size = entry.get("size")
            size_vram = entry.get("size_vram")
            ctx_len = entry.get("context_length", entry.get("context_size"))
            if isinstance(size, (int, float)) and size and size > 0:
                info["size"] = int(size)
            if isinstance(size_vram, (int, float)) and size_vram is not None:
                info["size_vram"] = int(size_vram)
            if info["size"] and info["size_vram"] is not None and info["size"] > 0:
                info["offload_ratio"] = info["size_vram"] / info["size"]
            if isinstance(ctx_len, (int, float)) and ctx_len and ctx_len > 0:
                info["context_length"] = int(ctx_len)
    except Exception:
        pass
    try:
        layers_gpu, layers_total = parse_offload_layers(server_log_slice(ctx))
        info["layers_gpu"] = layers_gpu
        info["layers_total"] = layers_total
    except Exception:
        pass
    try:
        ctx.load_info[tag] = info
    except Exception:
        pass
    return info


def enrich_perf_record(rec: dict, load_info: dict) -> dict:
    """Copy /api/ps offload fields into a PERF record (details + load_info)."""
    try:
        det = ((rec.get("verdict") or {}).get("details")) or {}
        for k in ("size", "size_vram", "offload_ratio", "context_length",
                  "layers_gpu", "layers_total"):
            if load_info.get(k) is not None:
                det[k] = load_info[k]
        rec["verdict"]["details"] = det
        rec["load_info"] = dict(load_info)
    except Exception:
        pass
    return rec


def _throttle_active(reason) -> bool:
    return envmod._throttle_active(reason)


def compute_resources(ctx: Ctx, t_start: float, t_end: float) -> dict:
    """Per-request resources from the Monitor ring buffer over [t_start, t_end].

    Falls back to a single nvidia snapshot only when the monitor has no
    samples in the window. vram_baseline_mb always comes from preflight.
    """
    baseline_mb = None
    try:
        baseline_mb = (getattr(ctx, "baseline", {}) or {}).get("vram_baseline_mb")
    except Exception:
        baseline_mb = None
    mon = getattr(ctx, "monitor", None)
    if mon is not None:
        try:
            stats = mon.window_stats(t_start, t_end)
        except Exception:
            stats = None
        if stats and stats.get("samples", 0) > 0:
            return {"vram_peak_mb": stats.get("vram_peak_mb"),
                    "vram_baseline_mb": baseline_mb,
                    "gpu_util_mean": stats.get("gpu_util_mean"),
                    "temp_start": stats.get("temp_start"),
                    "temp_peak": stats.get("temp_peak"),
                    "throttle": stats.get("throttle")}
    # fallback: one snapshot only
    try:
        snap = envmod.nvidia_snapshot()
    except Exception:
        snap = None
    if not snap:
        return {"vram_peak_mb": None, "vram_baseline_mb": baseline_mb,
                "gpu_util_mean": None, "temp_start": None,
                "temp_peak": None, "throttle": None}
    return {"vram_peak_mb": snap.get("vram_used_mb"),
            "vram_baseline_mb": baseline_mb,
            "gpu_util_mean": snap.get("gpu_util"),
            "temp_start": snap.get("temp_c"), "temp_peak": snap.get("temp_c"),
            "throttle": _throttle_active(snap.get("throttle_reasons"))}


def base_record(ctx: Ctx, tag: str, profile: Profile, test_id: str, ver: str,
                case_id: str, mode: str, invocation: dict) -> dict:
    return {"key": storemod.make_key(ctx.args.run_id, tag,
                                     ctx.digest_by_tag.get(tag, "unknown")[:12],
                                     test_id, ver, case_id, 0, mode,
                                     profile.profile_id or tag),
            "run_id": ctx.args.run_id, "attempt": 0,
            "identity": identity_for(ctx, tag),
            "invocation": invocation,
            "timestamps": {"utc": utc_now(), "local": local_now()}}


def single_block_record(ctx: Ctx, tag: str, profile: Profile, test_id: str, ver: str,
                        mode: str, status: str, reason: str, case_id: str = "__block__") -> dict:
    rec = base_record(ctx, tag, profile, test_id, ver, case_id, mode,
                      {"endpoint": "none", "raw": False, "think": None,
                       "options": {}, "num_ctx": 0, "num_predict": 0,
                       "prompt_sha256": "", "stop": []})
    rec["response"] = {"content": "", "thinking": "", "tool_calls": [],
                       "tool_call_channel": "none", "done_reason": None,
                       "prompt_eval_count": None, "eval_count": None}
    rec["timing"] = {"load_s": None, "ttft_s": None, "prompt_eval_s": None,
                     "eval_s": None, "prompt_tok_s": None, "gen_tok_s": None,
                     "wall_s": 0.0, "first_after_load": None}
    rec["resources"] = {"vram_peak_mb": None, "vram_baseline_mb": None,
                        "gpu_util_mean": None, "temp_start": None,
                        "temp_peak": None, "throttle": None}
    rec["verdict"] = {"status": status, "sub_reason": reason,
                      "attribution": "POLICY" if status in ("UNSUPPORTED_CAPABILITY",
                                                            "NOT_RUN_BUDGET") else "ENVIRONMENT",
                      "sem": 0.0, "strict": 0.0, "details": {}}
    rec["flags"] = []
    return rec


def record_block_crash(ctx: Ctx, tag: str, profile: Profile, test_id: str, exc: BaseException) -> None:
    """A crash inside one (model, test) block must not end the unattended run:
    log the traceback, store a HARNESS_ERROR block record (re-run on --resume), go on."""
    tb = traceback.format_exc()[-3000:]
    try:
        with open(os.path.join(ctx.run_dir, "block_errors.txt"), "a", encoding="utf-8") as f:
            f.write(f"=== {datetime.datetime.now().isoformat(timespec='seconds')} {tag} {test_id}\n{tb}\n")
    except Exception:
        pass
    try:
        meta = getattr(ctx.modules.get(test_id), "META", {}) or {}
        rec = single_block_record(ctx, tag, profile, test_id, meta.get("version", "n1"),
                                  meta.get("mode", "R0"), "HARNESS_ERROR",
                                  f"{type(exc).__name__}: {exc}"[:300])
        ctx.store.append(storemod.manifest_entry(ctx.run_dir, rec))
    except Exception:
        pass
    print(f"[block error] {tag} {test_id}: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------- one chat/vision call

def do_request(ctx: Ctx, profile: Profile, meta: dict, request: Request,
               think: bool | None, timeout_s: float,
               flags: list[str] | None = None) -> tuple[Response, dict, list[str]]:
    flags = list(flags or [])
    seed_src = getattr(ctx, "current_case_id", "")
    seed = zlib.crc32(seed_src.encode("utf-8")) & 0x7fffffff
    request = apply_system(profile, request)
    think_send = request.think if request.force_think else think
    if request.raw:
        think_send = None  # raw generate: no think key
    npred = num_predict_for(meta, bool(think_send))
    nctx = int(meta.get("num_ctx", 4096) or 4096)
    options, stop = resolve_options(profile, meta, request, think_send, npred, nctx, seed)
    invocation = {"endpoint": request.endpoint, "raw": bool(request.raw),
                  "think": think_send, "options": options, "num_ctx": nctx,
                  "num_predict": npred, "prompt_sha256": prompt_sha(request),
                  "stop": stop}
    t_left = ctx.deadline - time.time()
    timeout = max(1.0, min(timeout_s, t_left))
    if request.endpoint == "generate":
        resp = ctx.client.generate(profile.tag, request.prompt or "", options,
                                   raw=request.raw, stop=stop or None,
                                   think=think_send, timeout=timeout)
    else:
        resp = ctx.client.chat(profile.tag, request.messages or [], options,
                               think=think_send, tools=request.tools,
                               fmt=request.format, timeout=timeout,
                               stop=stop or None)
    return resp, invocation, flags


def finalize_response(ctx: Ctx, profile: Profile, meta: dict, case: Case,
                      resp: Response, invocation: dict,
                      flags: list[str], t_start: float | None = None,
                      t_end: float | None = None) -> dict:
    flags = list(flags)
    content, thinking, leaked = strip_think_leak(resp.content or "", resp.thinking or "")
    attribution = "NONE"
    if leaked:
        flags.append("THINK_LEAK")
        attribution = "RUNTIME"
    resp.content, resp.thinking = content, thinking
    channel = "native" if resp.tool_calls else "none"
    rec = base_record(ctx, profile.tag, profile, case.test_id,
                      meta.get("version", "n1"), case.id,
                      meta.get("mode", "R0"), invocation)
    rec["response"] = {"content": content, "thinking": thinking,
                       "tool_calls": resp.tool_calls or [],
                       "tool_call_channel": channel, "done_reason": resp.done_reason,
                       "prompt_eval_count": resp.prompt_eval_count,
                       "eval_count": resp.eval_count}
    rec["timing"] = {"load_s": resp.load_s, "ttft_s": resp.ttft_s,
                     "prompt_eval_s": resp.prompt_eval_s, "eval_s": resp.eval_s,
                     "prompt_tok_s": (resp.prompt_eval_count / resp.prompt_eval_s
                                      if resp.prompt_eval_count and resp.prompt_eval_s else None),
                     "gen_tok_s": (resp.eval_count / resp.eval_s
                                   if resp.eval_count and resp.eval_s else None),
                     "wall_s": resp.wall_s, "first_after_load": None}
    if t_start is not None and t_end is not None:
        rec["resources"] = compute_resources(ctx, t_start, t_end)
    else:
        rec["resources"] = compute_resources(ctx, time.time() - max(resp.wall_s or 0.0, 0.1),
                                             time.time())
    empty_ok = bool(meta.get("empty_ok", False))
    verdict: Verdict | None = None
    status = sub = None
    if resp.done_reason == "length":
        sub = "IN_THINKING" if not content else "IN_ANSWER"
        status = "OUTPUT_TRUNCATED"
    elif not content and not resp.tool_calls and not empty_ok:
        sub = "EMPTY_AFTER_THINKING" if thinking else "EMPTY"
        status = "EMPTY_OUTPUT"
    if status in ("OUTPUT_TRUNCATED", "EMPTY_OUTPUT"):
        sem = strict = 0.0
        details: dict = {}
        if status == "OUTPUT_TRUNCATED" and content:
            try:
                module = ctx.modules[case.test_id]
                v = module.validate(case, resp, profile)
                sem = float(v.sem)
                details = dict(v.details or {})
            except Exception as e:
                rec_tmp = {"validator_error": str(e)[:300]}
                details = rec_tmp
        normalized = Response(content=content, thinking=thinking,
                              tool_calls=resp.tool_calls, done_reason=resp.done_reason,
                              prompt_eval_count=resp.prompt_eval_count,
                              eval_count=resp.eval_count)
        _ = normalized
        rec["verdict"] = {"status": status, "sub_reason": sub,
                          "attribution": "MODEL",
                          "sem": sem, "strict": 0.0, "details": details}
        rec["flags"] = flags
        return rec
    # normal path -> validate()
    module = ctx.modules[case.test_id]
    nresp = Response(content=content, thinking=thinking, tool_calls=resp.tool_calls,
                     done_reason=resp.done_reason,
                     prompt_eval_count=resp.prompt_eval_count, eval_count=resp.eval_count,
                     load_s=resp.load_s, prompt_eval_s=resp.prompt_eval_s,
                     eval_s=resp.eval_s, ttft_s=resp.ttft_s, wall_s=resp.wall_s,
                     http_status=resp.http_status, raw=resp.raw)
    try:
        v = module.validate(case, nresp, profile)
        if leaked and attribution == "RUNTIME" and v.attribution == "NONE":
            v.attribution = "RUNTIME"
        rec["verdict"] = {"status": v.status, "sub_reason": v.sub_reason,
                          "attribution": v.attribution, "sem": float(v.sem),
                          "strict": float(v.strict), "details": v.details or {}}
    except Exception as e:
        rec["verdict"] = {"status": "VALIDATOR_ERROR",
                          "sub_reason": f"{type(e).__name__}: {e}"[:200],
                          "attribution": "VALIDATOR", "sem": 0.0, "strict": 0.0,
                          "details": {"trace": traceback.format_exc()[-2000:]}}
    rec["flags"] = flags
    return rec


def run_chat_case(ctx: Ctx, module, profile: Profile, meta: dict, case: Case,
                  think: bool | None, base_flags: list[str]) -> dict:
    ctx.current_case_id = case.id
    request = module.build_request(case, profile)
    timeout_s = float(meta.get("timeout_s", 120) or 120)
    attempt = 0
    while True:
        try:
            t0 = time.time()
            resp, invocation, flags = do_request(ctx, profile, meta, request, think,
                                                timeout_s, base_flags)
            t1 = time.time()
            rec = finalize_response(ctx, profile, meta, case, resp, invocation,
                                    flags, t0, t1)
            return rec
        except Exception as e:
            status, sub, attr = classify_exception(e)
            if status in RETRYABLE and attempt < 1:
                attempt += 1
                time.sleep(2.0)
                continue
            invocation = {"endpoint": getattr(request, "endpoint", "chat"),
                          "raw": bool(getattr(request, "raw", False)),
                          "think": think, "options": {}, "num_ctx": meta.get("num_ctx", 4096),
                          "num_predict": num_predict_for(meta, bool(think)),
                          "prompt_sha256": prompt_sha(request), "stop": []}
            rec = base_record(ctx, profile.tag, profile, case.test_id,
                              meta.get("version", "n1"), case.id,
                              meta.get("mode", "R0"), invocation)
            rec["attempt"] = attempt
            rec["response"] = {"content": "", "thinking": "", "tool_calls": [],
                               "tool_call_channel": "none", "done_reason": None,
                               "prompt_eval_count": None, "eval_count": None,
                               "error": str(e)[:500]}
            rec["timing"] = {"load_s": None, "ttft_s": None, "prompt_eval_s": None,
                             "eval_s": None, "prompt_tok_s": None, "gen_tok_s": None,
                             "wall_s": 0.0, "first_after_load": None}
            _base = (getattr(ctx, "baseline", {}) or {}).get("vram_baseline_mb")
            rec["resources"] = {"vram_peak_mb": None, "vram_baseline_mb": _base,
                                "gpu_util_mean": None, "temp_start": None,
                                "temp_peak": None, "throttle": None}
            rec["verdict"] = {"status": status, "sub_reason": sub,
                              "attribution": attr, "sem": 0.0, "strict": 0.0,
                              "details": {}}
            rec["flags"] = list(base_flags)
            return rec


# ---------------------------------------------------------------- tools_loop / embed

def make_chat_fn(ctx: Ctx, profile: Profile, meta: dict, think: bool | None,
                 base_flags: list[str]):
    def chat_fn(request: Request) -> Response:
        resp, _inv, _fl = do_request(ctx, profile, meta, request, think,
                                     float(meta.get("timeout_s", 120) or 120),
                                     base_flags)
        content, thinking, leaked = strip_think_leak(resp.content or "",
                                                     resp.thinking or "")
        resp.content, resp.thinking = content, thinking
        return resp
    return chat_fn


def run_tools_case(ctx: Ctx, module, profile: Profile, meta: dict, case: Case,
                   think: bool | None, base_flags: list[str]) -> dict:
    ctx.current_case_id = case.id
    chat_fn = make_chat_fn(ctx, profile, meta, think, base_flags)
    t0 = time.time()
    try:
        verdict, trace = module.run_case(case, profile, chat_fn)
        status = verdict.status
    except Exception as e:
        status, sub, attr = classify_exception(e)
        if status in RETRYABLE:
            try:
                verdict, trace = module.run_case(case, profile, chat_fn)
                status = verdict.status
            except Exception as e2:
                status2, sub2, attr2 = classify_exception(e2)
                return _runtime_record(ctx, profile, meta, case, think, e2,
                                       status2, sub2, attr2, base_flags)
        else:
            return _runtime_record(ctx, profile, meta, case, think, e,
                                   status, sub, attr, base_flags)
    t1 = time.time()
    rec = base_record(ctx, profile.tag, profile, case.test_id,
                      meta.get("version", "n1"), case.id, meta.get("mode", "R0"),
                      {"endpoint": "chat_loop", "raw": False, "think": think,
                       "options": {}, "num_ctx": meta.get("num_ctx", 4096),
                       "num_predict": num_predict_for(meta, bool(think)),
                       "prompt_sha256": "", "stop": list(profile.stop or [])})
    rec["response"] = {"content": "", "thinking": "", "tool_calls": [],
                       "tool_call_channel": "none", "done_reason": None,
                       "prompt_eval_count": None, "eval_count": None,
                       "trace": trace if isinstance(trace, list) else []}
    rec["timing"] = {"load_s": None, "ttft_s": None, "prompt_eval_s": None,
                     "eval_s": None, "prompt_tok_s": None, "gen_tok_s": None,
                     "wall_s": t1 - t0, "first_after_load": None}
    rec["resources"] = compute_resources(ctx, t0, t1)
    rec["verdict"] = {"status": verdict.status, "sub_reason": verdict.sub_reason,
                      "attribution": verdict.attribution, "sem": float(verdict.sem),
                      "strict": float(verdict.strict),
                      "details": verdict.details or {}}
    rec["flags"] = list(base_flags)
    return rec


def _runtime_record(ctx, profile, meta, case, think, exc, status, sub, attr,
                    base_flags) -> dict:
    rec = base_record(ctx, profile.tag, profile, case.test_id,
                      meta.get("version", "n1"), case.id, meta.get("mode", "R0"),
                      {"endpoint": "chat_loop", "raw": False, "think": think,
                       "options": {}, "num_ctx": meta.get("num_ctx", 4096),
                       "num_predict": num_predict_for(meta, bool(think)),
                       "prompt_sha256": "", "stop": []})
    rec["response"] = {"content": "", "thinking": "", "tool_calls": [],
                       "tool_call_channel": "none", "done_reason": None,
                       "prompt_eval_count": None, "eval_count": None,
                       "error": str(exc)[:500]}
    rec["timing"] = {"load_s": None, "ttft_s": None, "prompt_eval_s": None,
                     "eval_s": None, "prompt_tok_s": None, "gen_tok_s": None,
                     "wall_s": 0.0, "first_after_load": None}
    _base2 = (getattr(ctx, "baseline", {}) or {}).get("vram_baseline_mb")
    rec["resources"] = {"vram_peak_mb": None, "vram_baseline_mb": _base2,
                        "gpu_util_mean": None, "temp_start": None,
                        "temp_peak": None, "throttle": None}
    rec["verdict"] = {"status": status, "sub_reason": sub, "attribution": attr,
                      "sem": 0.0, "strict": 0.0, "details": {}}
    rec["flags"] = list(base_flags)
    return rec


def make_embed_fn(ctx: Ctx, profile: Profile, batch: int = 16):
    def embed_fn(texts: list[str]) -> Response:
        all_emb: list = []
        merged_raw: dict = {}
        wall = 0.0
        for i in range(0, len(texts), batch):
            chunk = texts[i:i + batch]
            t_left = ctx.deadline - time.time()
            r = ctx.client.embed(profile.tag, chunk,
                                 timeout=max(1.0, min(900.0, t_left)))
            wall += r.wall_s
            all_emb.extend(r.embeddings or [])
            merged_raw = r.raw
        return Response(wall_s=wall, http_status=200, raw=merged_raw,
                        embeddings=all_emb)
    return embed_fn


def run_embed_test(ctx: Ctx, module, profile: Profile, meta: dict,
                   cases: list[Case], think: bool | None,
                   base_flags: list[str]) -> list[dict]:
    embed_fn = make_embed_fn(ctx, profile)
    t0 = time.time()
    try:
        pairs = module.run_embed(cases, profile, embed_fn)
    except Exception as e:
        status, sub, attr = classify_exception(e)
        out = []
        for case in cases:
            out.append(_runtime_record(ctx, profile, meta, case, think, e,
                                       status, sub, attr, base_flags))
        return out
    t1 = time.time()
    out = []
    for case, verdict in pairs:
        rec = base_record(ctx, profile.tag, profile, case.test_id,
                          meta.get("version", "n1"), case.id,
                          meta.get("mode", "-"), {"endpoint": "embed",
                                                  "raw": False, "think": None,
                                                  "options": {},
                                                  "num_ctx": meta.get("num_ctx", 0),
                                                  "num_predict": 0, "prompt_sha256": "",
                                                  "stop": []})
        rec["response"] = {"content": "", "thinking": "", "tool_calls": [],
                           "tool_call_channel": "none", "done_reason": None,
                           "prompt_eval_count": None, "eval_count": None}
        rec["timing"] = {"load_s": None, "ttft_s": None, "prompt_eval_s": None,
                         "eval_s": None, "prompt_tok_s": None, "gen_tok_s": None,
                         "wall_s": 0.0, "first_after_load": None}
        rec["resources"] = compute_resources(ctx, t0, t1)
        rec["verdict"] = {"status": verdict.status, "sub_reason": verdict.sub_reason,
                          "attribution": verdict.attribution,
                          "sem": float(verdict.sem), "strict": float(verdict.strict),
                          "details": verdict.details or {}}
        rec["flags"] = list(base_flags)
        out.append(rec)
    # first embed batch loads the model -> capture /api/ps offload once
    try:
        capture_load_info(ctx, profile.tag)
    except Exception:
        pass
    return out


# ---------------------------------------------------------------- case loading

def load_cases_for(ctx: Ctx, test_id: str, fixtures_root: str) -> list[Case]:
    module = ctx.modules[test_id]
    fx = os.path.join(fixtures_root, test_id.replace("-", ""))  # e.g. HOME-20
    # fixtures dir is fixtures/HOME-XX; test_id "HOME-20" -> "HOME-20"
    fx = os.path.join(fixtures_root, test_id)
    if hasattr(module, "load_cases"):
        try:
            return module.load_cases(fx)
        except TypeError:
            return module.load_cases()
    # fallback: read cases.jsonl directly
    from bench.types import Case as _Case
    out = []
    with open(os.path.join(fx, "cases.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                out.append(_Case(id=d["id"], test_id=d.get("test_id", test_id),
                                 tier=d.get("tier", ""), lang=d.get("lang", "en"),
                                 input=d.get("input", {}), expected=d.get("expected"),
                                 meta=d.get("meta", {})))
    return out


# ---------------------------------------------------------------- PERF-lite

FILLER = ("The quick brown fox jumps over the lazy dog near the river bank. "
          "Pack my box with five dozen liquor jugs and a few extra sacks. ")


def filler_text(target_tokens: int) -> str:
    chars = target_tokens * 4
    reps = chars // len(FILLER) + 1
    return (FILLER * reps)[:chars]


def perf_chat_block(ctx: Ctx, profile: Profile, baseline: dict) -> tuple[list[dict], dict]:
    """2 cold loads + 1 fixed 128/128 + 3 warm 512/256. Returns (records, speeds)."""
    recs: list[dict] = []
    tag = profile.tag
    meta = {"version": "n1", "mode": "R0", "num_ctx": 4096, "timeout_s": 120,
            "num_predict": 128, "think_extra": 0}
    for i in range(2):
        # A cold load must start from an unloaded model (runtime + VRAM back to baseline).
        try:
            envmod.unload_all(ctx.client, baseline, timeout_s=60.0)
        except Exception:
            pass
        t0 = time.time()
        try:
            resp = ctx.client.generate(tag, "", {"num_ctx": 4096},
                                       keep_alive="30m", timeout=120.0)
            err = None
        except Exception as e:
            resp = None
            err = e
        wall = time.time() - t0
        rec = base_record(ctx, tag, profile, "PERF", "n1", f"perf_cold_{i + 1}",
                          "cold", {"endpoint": "generate", "raw": False,
                                   "think": None, "options": {"num_ctx": 4096},
                                   "num_ctx": 4096, "num_predict": 0,
                                   "prompt_sha256": hashlib.sha256(b"").hexdigest(),
                                   "stop": []})
        if resp is None:
            status, sub, attr = classify_exception(err, during_load=True)
            rec["verdict"] = {"status": status, "sub_reason": sub,
                              "attribution": attr, "sem": 0.0, "strict": 0.0,
                              "details": {"phase": "cold_load"}}
        else:
            rec["verdict"] = {"status": "OK", "sub_reason": "COLD_LOAD",
                              "attribution": "NONE", "sem": 1.0, "strict": 1.0,
                              "details": {"phase": "cold_load",
                                          "load_s": resp.load_s, "wall_s": wall}}
        rec["response"] = {"content": "", "thinking": "",
                           "tool_calls": [], "tool_call_channel": "none",
                           "done_reason": getattr(resp, "done_reason", None),
                           "prompt_eval_count": getattr(resp, "prompt_eval_count", None),
                           "eval_count": getattr(resp, "eval_count", None)}
        # Ollama's pure-load reply (done_reason "load") carries no load_duration -> use client wall time.
        rec["timing"] = {"load_s": (getattr(resp, "load_s", None) or wall) if resp is not None else None, "ttft_s": None,
                         "prompt_eval_s": None, "eval_s": None,
                         "prompt_tok_s": None, "gen_tok_s": None,
                         "wall_s": wall, "first_after_load": None}
        rec["resources"] = {"vram_peak_mb": None, "vram_baseline_mb": baseline.get("vram_baseline_mb"),
                            "gpu_util_mean": None, "temp_start": None,
                            "temp_peak": None, "throttle": None}
        rec["flags"] = []
        recs.append(rec)
    # 1 fixed request: 128-token prompt, num_predict 128
    prompt128 = filler_text(128)
    try:
        t0 = time.time()
        resp = ctx.client.generate(tag, prompt128,
                                   {"num_ctx": 4096, "num_predict": 128,
                                    "temperature": 0.0, "top_p": 1.0},
                                   timeout=180.0)
        wall = time.time() - t0
        ok = {"status": "OK", "sub_reason": "PERF_FIXED", "attribution": "NONE",
              "sem": 1.0, "strict": 1.0,
              "details": {"phase": "fixed_128", "load_s": resp.load_s,
                          "ttft_s": resp.ttft_s, "eval_count": resp.eval_count,
                          "eval_s": resp.eval_s}}
    except Exception as e:
        wall = 0.0
        resp = None
        status, sub, attr = classify_exception(e)
        ok = {"status": status, "sub_reason": sub, "attribution": attr,
              "sem": 0.0, "strict": 0.0, "details": {"phase": "fixed_128"}}
    rec = base_record(ctx, tag, profile, "PERF", "n1", "perf_fixed_128", "warm",
                      {"endpoint": "generate", "raw": False, "think": False,
                       "options": {"num_ctx": 4096, "num_predict": 128},
                       "num_ctx": 4096, "num_predict": 128,
                       "prompt_sha256": hashlib.sha256(prompt128.encode()).hexdigest(),
                       "stop": []})
    rec["response"] = {"content": "", "thinking": "", "tool_calls": [],
                       "tool_call_channel": "none",
                       "done_reason": getattr(resp, "done_reason", None) if resp else None,
                       "prompt_eval_count": getattr(resp, "prompt_eval_count", None) if resp else None,
                       "eval_count": getattr(resp, "eval_count", None) if resp else None}
    rec["timing"] = {"load_s": getattr(resp, "load_s", None) if resp else None,
                     "ttft_s": getattr(resp, "ttft_s", None) if resp else None,
                     "prompt_eval_s": getattr(resp, "prompt_eval_s", None) if resp else None,
                     "eval_s": getattr(resp, "eval_s", None) if resp else None,
                     "prompt_tok_s": None, "gen_tok_s": None, "wall_s": wall,
                     "first_after_load": None}
    rec["resources"] = {"vram_peak_mb": None, "vram_baseline_mb": baseline.get("vram_baseline_mb"),
                        "gpu_util_mean": None, "temp_start": None,
                        "temp_peak": None, "throttle": None}
    rec["verdict"] = ok
    rec["flags"] = []
    recs.append(rec)
    # 3 warm: ~512-token prompt, num_predict 256
    speeds_g, speeds_p = [], []
    prompt512 = filler_text(512)
    base512 = prompt512
    for i in range(3):
        # distinct first tokens: identical prompts hit the prompt cache and inflate prompt_tok_s
        prompt512 = f"Sample {i + 1} of 3. " + base512
        try:
            t0 = time.time()
            resp = ctx.client.generate(tag, prompt512,
                                       {"num_ctx": 4096, "num_predict": 256,
                                        "temperature": 0.0, "top_p": 1.0},
                                       timeout=240.0)
            wall = time.time() - t0
            if resp.eval_count and resp.eval_s:
                speeds_g.append(resp.eval_count / resp.eval_s)
            if resp.prompt_eval_count and resp.prompt_eval_s:
                speeds_p.append(resp.prompt_eval_count / resp.prompt_eval_s)
            ok = {"status": "OK", "sub_reason": "PERF_WARM", "attribution": "NONE",
                  "sem": 1.0, "strict": 1.0,
                  "details": {"phase": "warm", "ttft_s": resp.ttft_s,
                              "prompt_tok_s": (resp.prompt_eval_count / resp.prompt_eval_s
                                               if resp.prompt_eval_count and resp.prompt_eval_s else None),
                              "gen_tok_s": (resp.eval_count / resp.eval_s
                                            if resp.eval_count and resp.eval_s else None)}}
        except Exception as e:
            wall = 0.0
            resp = None
            status, sub, attr = classify_exception(e)
            ok = {"status": status, "sub_reason": sub, "attribution": attr,
                  "sem": 0.0, "strict": 0.0, "details": {"phase": "warm"}}
        rec = base_record(ctx, tag, profile, "PERF", "n1", f"perf_warm_{i + 1}",
                          "warm", {"endpoint": "generate", "raw": False,
                                   "think": False,
                                   "options": {"num_ctx": 4096, "num_predict": 256},
                                   "num_ctx": 4096, "num_predict": 256,
                                   "prompt_sha256": hashlib.sha256(prompt512.encode()).hexdigest(),
                                   "stop": []})
        rec["response"] = {"content": "", "thinking": "", "tool_calls": [],
                           "tool_call_channel": "none",
                           "done_reason": getattr(resp, "done_reason", None) if resp else None,
                           "prompt_eval_count": getattr(resp, "prompt_eval_count", None) if resp else None,
                           "eval_count": getattr(resp, "eval_count", None) if resp else None}
        rec["timing"] = {"load_s": None,
                         "ttft_s": getattr(resp, "ttft_s", None) if resp else None,
                         "prompt_eval_s": getattr(resp, "prompt_eval_s", None) if resp else None,
                         "eval_s": getattr(resp, "eval_s", None) if resp else None,
                         "prompt_tok_s": None, "gen_tok_s": None, "wall_s": wall,
                         "first_after_load": None}
        rec["resources"] = {"vram_peak_mb": None, "vram_baseline_mb": baseline.get("vram_baseline_mb"),
                            "gpu_util_mean": None, "temp_start": None,
                            "temp_peak": None, "throttle": None}
        rec["verdict"] = ok
        rec["flags"] = []
        recs.append(rec)
    speeds = {"gen_tok_s": (sum(speeds_g) / len(speeds_g)) if speeds_g else 5.0,
              "prompt_tok_s": (sum(speeds_p) / len(speeds_p)) if speeds_p else 50.0}
    # FIX_A.3: after cold loads the model is resident -> capture /api/ps offload
    try:
        load_info = capture_load_info(ctx, tag)
        for rec in recs:
            enrich_perf_record(rec, load_info)
    except Exception:
        pass
    for r in recs:
        t, rp = r.get("timing") or {}, r.get("response") or {}
        pe, ev = rp.get("prompt_eval_count"), rp.get("eval_count")
        if pe and t.get("prompt_eval_s"):
            t["prompt_tok_s"] = pe / t["prompt_eval_s"]
        if ev and t.get("eval_s"):
            t["gen_tok_s"] = ev / t["eval_s"]
    return recs, speeds


def perf_embed_block(ctx: Ctx, profile: Profile, baseline: dict) -> tuple[list[dict], dict]:
    """PERF-EMB-lite: 2 cold loads, 3 warm batches of 16, 10 single-query latencies."""
    recs: list[dict] = []
    tag = profile.tag
    texts16 = [filler_text(40) + f" doc {i}" for i in range(16)]
    for i in range(2):
        t0 = time.time()
        try:
            r = ctx.client.embed(tag, ["warmup probe"], timeout=120.0)
            wall = time.time() - t0
            ok = {"status": "OK", "sub_reason": "COLD_LOAD", "attribution": "NONE",
                  "sem": 1.0, "strict": 1.0,
                  "details": {"phase": "cold_load", "wall_s": wall,
                              "n_vec": len(r.embeddings or [])}}
        except Exception as e:
            wall = time.time() - t0
            status, sub, attr = classify_exception(e, during_load=True)
            ok = {"status": status, "sub_reason": sub, "attribution": attr,
                  "sem": 0.0, "strict": 0.0, "details": {"phase": "cold_load"}}
        recs.append(_perf_rec(ctx, profile, f"perf_emb_cold_{i + 1}", "cold", wall,
                              baseline, ok))
    lat = []
    for i in range(3):
        t0 = time.time()
        try:
            r = ctx.client.embed(tag, texts16, timeout=300.0)
            wall = time.time() - t0
            lat.append(wall)
            ok = {"status": "OK", "sub_reason": "PERF_WARM", "attribution": "NONE",
                  "sem": 1.0, "strict": 1.0,
                  "details": {"phase": "warm_batch16", "wall_s": wall,
                              "n_vec": len(r.embeddings or [])}}
        except Exception as e:
            wall = time.time() - t0
            status, sub, attr = classify_exception(e)
            ok = {"status": status, "sub_reason": sub, "attribution": attr,
                  "sem": 0.0, "strict": 0.0, "details": {"phase": "warm_batch16"}}
        recs.append(_perf_rec(ctx, profile, f"perf_emb_warm_{i + 1}", "warm", wall,
                              baseline, ok))
    qlat = []
    for i in range(10):
        t0 = time.time()
        try:
            ctx.client.embed(tag, [f"query probe {i} " + filler_text(10)],
                             timeout=120.0)
            qlat.append(time.time() - t0)
        except Exception:
            pass
    import statistics
    speeds = {"gen_tok_s": 1000.0, "prompt_tok_s": 1000.0,
              "emb_batch_s": (sum(lat) / len(lat)) if lat else 5.0,
              "emb_query_s": (statistics.median(qlat)) if qlat else 0.5}
    recs.append(_perf_rec(ctx, profile, "perf_emb_queries", "warm",
                          sum(qlat), baseline,
                          {"status": "OK", "sub_reason": "PERF_QUERIES",
                           "attribution": "NONE", "sem": 1.0, "strict": 1.0,
                           "details": {"phase": "queries",
                                       "median_query_s": speeds["emb_query_s"],
                                       "n": len(qlat)}}))
    try:
        load_info = capture_load_info(ctx, tag)
        for rec in recs:
            enrich_perf_record(rec, load_info)
    except Exception:
        pass
    return recs, speeds


def _perf_rec(ctx, profile, case_id, mode, wall, baseline, verdict) -> dict:
    rec = base_record(ctx, profile.tag, profile, "PERF", "n1", case_id, mode,
                      {"endpoint": "embed", "raw": False, "think": None,
                       "options": {}, "num_ctx": 0, "num_predict": 0,
                       "prompt_sha256": "", "stop": []})
    rec["response"] = {"content": "", "thinking": "", "tool_calls": [],
                       "tool_call_channel": "none", "done_reason": None,
                       "prompt_eval_count": None, "eval_count": None}
    rec["timing"] = {"load_s": None, "ttft_s": None, "prompt_eval_s": None,
                     "eval_s": None, "prompt_tok_s": None, "gen_tok_s": None,
                     "wall_s": wall, "first_after_load": None}
    rec["resources"] = {"vram_peak_mb": None,
                        "vram_baseline_mb": baseline.get("vram_baseline_mb"),
                        "gpu_util_mean": None, "temp_start": None,
                        "temp_peak": None, "throttle": None}
    rec["verdict"] = verdict
    rec["flags"] = []
    return rec


# ---------------------------------------------------------------- scheduling

def eligible_tests_for(ctx: Ctx, tag: str, test_ids: list[str]) -> tuple[list[str], dict]:
    elig_ok, elig_other = [], {}
    for tid in test_ids:
        info = (ctx.elig.get(tid, {}) or {}).get(tag)
        if info and info.get("code") == "E":
            elig_ok.append(tid)
        else:
            elig_other[tid] = info or {"code": "U", "reason": "no eligibility entry"}
    return elig_ok, elig_other


def estimate_block_s(ctx: Ctx, profile: Profile, meta: dict, n_cases: int) -> float:
    """Per-(model,test) estimate (FIX_A.5).

    Measured path: per_case = median wall_s of the home model's HOME cases
      * (home gen_tok_s / this model gen_tok_s), clipped to
      [min_case_s, META.timeout_s]; tools_loop multiplies by 3.
    Fallback: previous formula with 0.5 * num_predict.
    """
    from bench.types import MODEL_OUTCOME
    import statistics as _st
    min_case = float(getattr(getattr(ctx, "args", None), "min_case_s", 5.0) or 5.0)
    timeout = float(meta.get("timeout_s", 120) or 120)
    kind = meta.get("kind")
    if kind == "embed":
        per_case = 30.0
        per_case = max(min_case, min(per_case, timeout))
        return n_cases * per_case + 20.0
    # measured path
    try:
        test_id = meta.get("id")
        home_tag = None
        try:
            inv = {v: k for k, v in
                   registrymod.home_model_map(getattr(ctx, "modules", {}) or {}).items()}
            home_tag = inv.get(test_id) if test_id else None
        except Exception:
            home_tag = None
        gen_this = (getattr(ctx, "speeds", {}).get(profile.tag, {}) or {}).get("gen_tok_s")
        gen_home = (getattr(ctx, "speeds", {}).get(home_tag, {}) or {}).get("gen_tok_s") if home_tag else None
        if (home_tag and test_id and gen_this and gen_home
                and gen_this > 0 and gen_home > 0):
            walls: list[float] = []
            try:
                all_recs = ctx.store.load_all() if hasattr(ctx.store, "load_all") else []
            except Exception:
                all_recs = []
            for r in all_recs:
                try:
                    key = str(r.get("key", ""))
                    parts = key.split("|")
                    if len(parts) < 5:
                        continue
                    rtag = parts[2].split("@")[0]
                    rtest = parts[3].split("@")[0]
                    if rtag != home_tag or rtest != test_id:
                        continue
                    if ((r.get("verdict") or {}).get("status")) not in MODEL_OUTCOME:
                        continue
                    w = (r.get("timing") or {}).get("wall_s")
                    if isinstance(w, (int, float)) and w and w > 0:
                        walls.append(float(w))
                except Exception:
                    continue
            if walls:
                med = _st.median(walls)
                per_case = med * (float(gen_home) / float(gen_this))
                if kind == "tools_loop":
                    per_case *= 3.0
                per_case = max(min_case, min(per_case, timeout))
                return n_cases * per_case + 20.0
    except Exception:
        pass
    # fallback: previous formula with 0.5 * num_predict
    speed = ctx.speeds.get(profile.tag, {}).get("gen_tok_s", 5.0) or 5.0
    pspeed = ctx.speeds.get(profile.tag, {}).get("prompt_tok_s", 50.0) or 50.0
    npred = num_predict_for(meta, meta.get("mode") == "R1")
    per_case = (0.5 * npred) / max(speed, 0.1) + 1500.0 / max(pspeed, 1.0) + 8.0
    if kind == "tools_loop":
        per_case *= 3.0
    per_case = max(min_case, min(per_case, timeout))
    return n_cases * per_case + 20.0


def run_test_block(ctx: Ctx, profile: Profile, test_id: str, cases: list[Case],
                   fixtures_root: str, smoke: bool = False) -> None:
    module = ctx.modules[test_id]
    meta = dict(module.META)
    think, flags = resolve_think(profile, meta.get("mode", "R0"))
    if smoke:
        cases = cases[:2]
    kind = meta.get("kind")
    if kind == "embed":
        for rec in run_embed_test(ctx, module, profile, meta, cases, think, flags):
            ctx.store.append(storemod.manifest_entry(ctx.run_dir, rec))
        return
    first = True
    for case in cases:
        if time.time() >= ctx.deadline:
            rec = single_block_record(ctx, profile.tag, profile, test_id,
                                      meta.get("version", "n1"),
                                      meta.get("mode", "R0"),
                                      "NOT_RUN_BUDGET", "DEADLINE_REACHED",
                                      case_id=case.id)
            ctx.store.append(storemod.manifest_entry(ctx.run_dir, rec))
            continue
        if kind == "tools_loop":
            rec = run_tools_case(ctx, module, profile, meta, case, think, flags)
        else:
            rec = run_chat_case(ctx, module, profile, meta, case, think, flags)
        ctx.store.append(storemod.manifest_entry(ctx.run_dir, rec))
        if first:
            first = False
            # FIX_A.3: first request of each model block loads the model
            try:
                capture_load_info(ctx, profile.tag)
            except Exception:
                pass


def budget_exceeded_block(ctx: Ctx, profile: Profile, meta: dict, n_cases: int) -> bool:
    est = estimate_block_s(ctx, profile, meta, n_cases)
    return (time.time() + est) > (ctx.deadline - 600.0)


# ---------------------------------------------------------------- manifest

def write_run_manifest(ctx: Ctx, args, project_root: str, model_order: list[str],
                       fingerprint: dict, preflight: dict) -> dict:
    bench_files = storemod.collect_files(os.path.join(project_root, "bench"))
    gen_files = storemod.collect_files(os.path.join(project_root, "gen"))
    cfg_files = storemod.collect_files(os.path.join(project_root, "config"))
    hashes: dict = {}
    for rel in bench_files:
        hashes["bench/" + rel] = storemod.sha256_file(
            os.path.join(project_root, "bench", rel.replace("/", os.sep)))
    for rel in gen_files:
        hashes["gen/" + rel] = storemod.sha256_file(
            os.path.join(project_root, "gen", rel.replace("/", os.sep)))
    for rel in cfg_files:
        hashes["config/" + rel] = storemod.sha256_file(
            os.path.join(project_root, "config", rel.replace("/", os.sep)))
    fx_manifests: dict = {}
    fx_root = os.path.join(project_root, "fixtures")
    if os.path.isdir(fx_root):
        for entry in sorted(os.listdir(fx_root)):
            mp = os.path.join(fx_root, entry, "manifest.json")
            if os.path.isfile(mp):
                fx_manifests[entry] = storemod.sha256_file(mp)
    man = {"run_id": args.run_id, "start_utc": utc_now(), "start_local": local_now(),
           "budget_hours": args.budget_hours, "base_url": base_url(),
           "file_hashes": hashes, "fixture_manifests": fx_manifests,
           "model_digests": ctx.digest_by_tag, "ollama_version": ctx.ollama_version,
           "fingerprint": fingerprint, "preflight": preflight,
           "model_order": model_order, "smoke": bool(args.smoke),
           "load_info": getattr(ctx, "load_info", {}),
           "model_sizes": getattr(ctx, "size_by_tag", {})}
    with open(os.path.join(ctx.run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
    return man


def verify_against_manifest(ctx: Ctx, project_root: str) -> None:
    mp = os.path.join(ctx.run_dir, "manifest.json")
    if not os.path.exists(mp):
        raise RuntimeError(f"resume: manifest not found in {ctx.run_dir}")
    with open(mp, encoding="utf-8") as f:
        man = json.load(f)
    old = man.get("file_hashes", {})
    bench_files = storemod.collect_files(os.path.join(project_root, "bench"))
    gen_files = storemod.collect_files(os.path.join(project_root, "gen"))
    cfg_files = storemod.collect_files(os.path.join(project_root, "config"))
    cur: dict = {}
    for rel in bench_files:
        cur["bench/" + rel] = storemod.sha256_file(
            os.path.join(project_root, "bench", rel.replace("/", os.sep)))
    for rel in gen_files:
        cur["gen/" + rel] = storemod.sha256_file(
            os.path.join(project_root, "gen", rel.replace("/", os.sep)))
    for rel in cfg_files:
        cur["config/" + rel] = storemod.sha256_file(
            os.path.join(project_root, "config", rel.replace("/", os.sep)))
    if cur != old:
        added = sorted(set(cur) - set(old))
        removed = sorted(set(old) - set(cur))
        changed = sorted(k for k in set(cur) & set(old) if cur[k] != old[k])
        raise RuntimeError(f"resume refused: code changed since run "
                           f"(added={added} removed={removed} changed={changed})")


# ---------------------------------------------------------------- main

SMOKE_DEFAULT_MODELS = ["qwen3:1.7b", "functiongemma:270m",
                        "nomic-embed-text:latest", "granite3.2-vision:2b",
                        "reader-lm:1.5b", "nuextract:3.8b"]


def parse_args(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="NIGHT-1 benchmark runner")
    p.add_argument("--budget-hours", type=float, default=8.0)
    p.add_argument("--run-id", default=None)
    p.add_argument("--resume", default=None)
    p.add_argument("--models", default=None,
                   help="comma-separated tags, or tag: prefix filters")
    p.add_argument("--tests", default=None, help="comma-separated HOME-.. ids")
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--phase", default="all", choices=["all", "1", "2", "3"])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--min-case-s", type=float, default=5.0,
                   help="floor for per-case budget estimate in seconds")
    p.add_argument("--fixtures", default=None)
    p.add_argument("--results-root", default=None)
    p.add_argument("--profiles", default=None)
    p.add_argument("--eligibility", default=None)
    p.add_argument("--tests-dir", default=None)
    return p.parse_args(argv)


def select_models(profiles: dict, models_arg: str | None, smoke: bool,
                  size_by_tag: dict | None = None) -> list[str]:
    if models_arg:
        wanted: list[str] = []
        for m in models_arg.split(","):
            m = m.strip()
            if m in profiles:
                wanted.append(m)
            else:
                wanted += [t for t in profiles if t.startswith(m)]
        return wanted
    if smoke:
        return [t for t in SMOKE_DEFAULT_MODELS if t in profiles]
    if size_by_tag:
        # FIX_A.4: order by actual model size in bytes from /api/tags
        known = [t for t in profiles if t in size_by_tag]
        unknown = [t for t in profiles if t not in size_by_tag]
        known_sorted = sorted(known, key=lambda t: (size_by_tag[t], t))
        unknown_sorted = sorted(unknown, key=lambda t: (model_size_gb(t), t))
        return known_sorted + unknown_sorted
    return sorted(profiles, key=lambda t: (model_size_gb(t), t))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
    # normalize: bench/runner.py -> parent is project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if args.smoke and args.budget_hours == 8.0:
        args.budget_hours = 20.0 / 60.0
    if args.run_id is None:
        args.run_id = args.resume or ("smoke-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                                      if args.smoke else "night-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    results_root = args.results_root or os.path.join(project_root, "results")
    fixtures_root = args.fixtures or os.path.join(project_root, "fixtures")
    run_dir = os.path.join(results_root, args.run_id)

    profiles = load_profiles(args.profiles)
    modules = registrymod.discover(args.tests_dir)
    elig = load_eligibility(args.eligibility)
    test_ids = sorted(modules)
    if args.tests:
        want = {t.strip() for t in args.tests.split(",") if t.strip()}
        test_ids = [t for t in test_ids if t in want]

    # ---------------- dry run: plan only, no requests ----------------
    if args.dry_run:
        model_tags = select_models(profiles, args.models, args.smoke)
        print(f"run_id={args.run_id} budget_hours={args.budget_hours} "
              f"models={len(model_tags)} tests={len(test_ids)}")
        total_est = 0.0
        for tag in model_tags:
            prof = profiles[tag]
            ok, other = eligible_tests_for_fake(elig, tag, test_ids)
            home_tid = next((tid for tid in ok
                             if modules[tid].META.get("home") == tag), None)
            print(f"- {tag}: eligible={len(ok)} unsupported={len(other)} "
                  f"home={home_tid}")
            for tid in ok:
                meta = modules[tid].META
                n = 2 if args.smoke else 12
                print(f"    {tid} kind={meta['kind']} mode={meta['mode']} "
                      f"core_n={meta['core_n']} timeout={meta['timeout_s']}")
                total_est += n * 30.0
        print(f"estimated_min={total_est / 60.0:.1f} (rough, 30 s/case)")
        return 0

    # ---------------- live run ----------------
    envmod.set_thread_execution_state(True)
    os.makedirs(run_dir, exist_ok=True)
    store = storemod.Store(run_dir)
    client = OllamaClient(timeout=120.0)
    deadline = time.time() + float(args.budget_hours) * 3600.0
    ctx = Ctx(args, run_dir, modules, profiles, elig, client, store, deadline)
    # telemetry monitor (ring buffer, CSV) for per-request resources
    try:
        ctx.monitor = envmod.Monitor(os.path.join(run_dir, "telemetry.csv"))
        ctx.monitor.start()
    except Exception:
        ctx.monitor = None
    report_error = None
    try:
        if args.resume:
            verify_against_manifest(ctx, project_root)
        # identity + actual sizes for Phase-1 ordering (FIX_A.4)
        try:
            ctx.ollama_version = client.version()
            tag_entries = client.tags()
            for t in tag_entries:
                name = t.get("name", "")
                ctx.digest_by_tag[name] = t.get("digest", "unknown")
            ctx.size_by_tag = fetch_size_map(client)
        except Exception:
            pass
        # Phase 0: preflight
        fp = envmod.fingerprint(client)
        fast = os.environ.get("BENCH_FAST_PREFLIGHT") == "1" or args.smoke
        baseline = envmod.idle_baseline(5.0 if fast else 30.0, 1.0)
        ctx.baseline = baseline
        cont_ok, cont_info = envmod.contention_check(
            baseline, wait_s=30.0 if fast else 600.0)
        preflight = {"fingerprint": fp, "baseline": baseline,
                     "contention": {"ok": cont_ok, "info": cont_info}}
        with open(os.path.join(run_dir, "preflight.json"), "w",
                   encoding="utf-8") as f:
            json.dump(preflight, f, ensure_ascii=False, indent=1)
        # model order: ascending ACTUAL size from /api/tags (FIX_A.4), recorded
        model_tags = select_models(profiles, args.models, args.smoke,
                                   getattr(ctx, "size_by_tag", None))
        if args.phase == "all" or args.phase == "1":
            pass  # order stays size-ascending
        done_keys = store.existing_keys()
        if args.resume:
            # drop keys that must be re-run (ours / NOT_RUN_BUDGET / non-final)
            keep = set()
            by_key = store.records_by_key()
            for k, r in by_key.items():
                st = ((r.get("verdict") or {}).get("status"))
                if storemod.is_final_status(st):
                    keep.add(k)
            done_keys = keep
        write_run_manifest(ctx, args, project_root, model_tags, fp,
                           {"baseline": baseline,
                            "contention": {"ok": cont_ok, "info": cont_info}})
        home_map = registrymod.home_model_map(modules)
        # ---- Phase 1: perf + own HOME test, all cases ----
        if args.phase in ("all", "1"):
            for tag in model_tags:
                if time.time() >= deadline:
                    break
                prof = profiles[tag]
                try:
                    ok_u, info_u = envmod.unload_all(client, baseline)
                    if not ok_u:
                        ctx.unload_failed_tags.add(tag)
                    envmod.thermal_gate((baseline.get("idle_temp_c") or 45.0))
                    meta_perf = {"timeout_s": 240}
                    if prof.kind == "embed":
                        recs, speeds = perf_embed_block(ctx, prof, baseline)
                    else:
                        recs, speeds = perf_chat_block(ctx, prof, baseline)
                    ctx.speeds[tag] = speeds
                    for rec in recs:
                        if rec["key"] not in done_keys:
                            store.append(storemod.manifest_entry(run_dir, rec))
                    # own HOME test
                    home_tid = home_map.get(tag)
                    if home_tid and home_tid in test_ids:
                        info = (elig.get(home_tid, {}) or {}).get(tag, {})
                        if info.get("code") != "E":
                            rec = single_block_record(
                                ctx, tag, prof, home_tid,
                                modules[home_tid].META.get("version", "n1"),
                                modules[home_tid].META.get("mode", "R0"),
                                "UNSUPPORTED_CAPABILITY",
                                str(info.get("reason", "not eligible"))[:300])
                            if rec["key"] not in done_keys:
                                store.append(storemod.manifest_entry(run_dir, rec))
                        else:
                            cases = load_cases_for(ctx, home_tid, fixtures_root)
                            planned = cases[:2] if args.smoke else cases
                            hmeta = modules[home_tid].META  # resume: skip cases already final
                            planned = [c for c in planned if _case_key(ctx, tag, prof, home_tid, hmeta, c)
                                       not in done_keys]
                            if not planned:
                                pass
                            elif budget_exceeded_block(ctx, prof,
                                                     modules[home_tid].META, len(planned)):
                                rec = single_block_record(
                                    ctx, tag, prof, home_tid,
                                    modules[home_tid].META.get("version", "n1"),
                                    modules[home_tid].META.get("mode", "R0"),
                                    "NOT_RUN_BUDGET", "BLOCK_ESTIMATE_EXCEEDS_DEADLINE")
                                if rec["key"] not in done_keys:
                                    store.append(storemod.manifest_entry(run_dir, rec))
                            else:
                                run_test_block(ctx, prof, home_tid, planned,
                                               fixtures_root, smoke=args.smoke)
                except Exception as _e:  # noqa: BLE001 - one block must not end the night run
                    record_block_crash(ctx, tag, prof, home_map.get(tag) or "PERF", _e)
                # refresh done keys
                done_keys = store.existing_keys()
        # ---- Phase 2: away runs on core subsets, fast models first ----
        if args.phase in ("all", "2"):
            order2 = sorted(model_tags,
                            key=lambda t: (-ctx.speeds.get(t, {}).get("gen_tok_s", 0.0), t))
            # fast first -> descending speed; unknown (0.0) last
            order2 = sorted(model_tags,
                            key=lambda t: (ctx.speeds.get(t, {}).get("gen_tok_s", 0.0) == 0.0,
                                           -ctx.speeds.get(t, {}).get("gen_tok_s", 0.0), t))
            home_map2 = registrymod.home_model_map(modules)
            for tag in order2:
                if time.time() >= deadline:
                    break
                prof = profiles[tag]
                away = [t for t in test_ids if home_map2.get(tag) != t]
                away_ok, away_other = eligible_tests_for(ctx, tag, away)
                for tid in sorted(away_other):
                    info = away_other[tid]
                    rec = single_block_record(
                        ctx, tag, prof, tid,
                        modules[tid].META.get("version", "n1"),
                        modules[tid].META.get("mode", "R0"),
                        "UNSUPPORTED_CAPABILITY",
                        str(info.get("reason", info.get("code", "U")))[:300])
                    if rec["key"] not in done_keys:
                        store.append(storemod.manifest_entry(run_dir, rec))
                if not away_ok:
                    continue
                envmod.unload_all(client, baseline)
                # group tests by num_ctx so one load covers each group
                away_ok = sorted(away_ok,
                                 key=lambda t: (modules[t].META.get("num_ctx", 4096), t))
                for tid in away_ok:
                    if time.time() >= deadline:
                        break
                    try:
                        meta = modules[tid].META
                        cases = load_cases_for(ctx, tid, fixtures_root)
                        core = cases[:int(meta.get("core_n", len(cases)))]
                        if args.smoke:
                            core = core[:2]
                        # skip already-done cases
                        todo = [c for c in core if _case_key(ctx, tag, prof, tid, meta, c)
                                not in done_keys]
                        if not todo:
                            continue
                        if budget_exceeded_block(ctx, prof, meta, len(todo)):
                            for c in todo:
                                rec = single_block_record(
                                    ctx, tag, prof, tid, meta.get("version", "n1"),
                                    meta.get("mode", "R0"), "NOT_RUN_BUDGET",
                                    "BLOCK_ESTIMATE_EXCEEDS_DEADLINE", case_id=c.id)
                                store.append(storemod.manifest_entry(run_dir, rec))
                            continue
                        run_test_block(ctx, prof, tid, todo, fixtures_root,
                                       smoke=args.smoke)
                        done_keys = store.existing_keys()
                    except Exception as _e:  # noqa: BLE001 - one block must not end the night run
                        record_block_crash(ctx, tag, prof, tid, _e)
        # ---- Phase 3: remaining away cases ----
        if args.phase in ("all", "3"):
            order3 = sorted(model_tags,
                            key=lambda t: (ctx.speeds.get(t, {}).get("gen_tok_s", 0.0) == 0.0,
                                           -ctx.speeds.get(t, {}).get("gen_tok_s", 0.0), t))
            for tag in order3:
                if time.time() >= deadline:
                    break
                prof = profiles[tag]
                away = [t for t in test_ids if home_map.get(tag) != t]
                away_ok, _ = eligible_tests_for(ctx, tag, away)
                for tid in sorted(away_ok, key=lambda t: (modules[t].META.get("num_ctx", 4096), t)):
                    if time.time() >= deadline:
                        break
                    try:
                        meta = modules[tid].META
                        cases = load_cases_for(ctx, tid, fixtures_root)
                        core_n = int(meta.get("core_n", len(cases)))
                        rest = cases[core_n:]
                        if args.smoke or not rest:
                            continue
                        todo = [c for c in rest if _case_key(ctx, tag, prof, tid, meta, c)
                                not in done_keys]
                        if not todo:
                            continue
                        if budget_exceeded_block(ctx, prof, meta, len(todo)):
                            for c in todo:
                                rec = single_block_record(
                                    ctx, tag, prof, tid, meta.get("version", "n1"),
                                    meta.get("mode", "R0"), "NOT_RUN_BUDGET",
                                    "BLOCK_ESTIMATE_EXCEEDS_DEADLINE", case_id=c.id)
                                store.append(storemod.manifest_entry(run_dir, rec))
                            continue
                        run_test_block(ctx, prof, tid, todo, fixtures_root)
                        done_keys = store.existing_keys()
                    except Exception as _e:  # noqa: BLE001 - one block must not end the night run
                        record_block_crash(ctx, tag, prof, tid, _e)
    except KeyboardInterrupt:
        report_error = "interrupted by user"
    except Exception as e:  # noqa: BLE001
        report_error = f"{type(e).__name__}: {e}\n{traceback.format_exc()[-3000:]}"
        with open(os.path.join(run_dir, "runner_error.txt"), "w",
                   encoding="utf-8") as f:
            f.write(report_error)
    finally:
        try:
            if getattr(ctx, "monitor", None) is not None:
                try:
                    ctx.monitor.stop()
                    ctx.monitor.join(timeout=5.0)
                except Exception:
                    pass
        except Exception:
            pass
        try:  # leave the GPU free after the run (requests use keep_alive=30m)
            if getattr(ctx, "client", None) is not None:
                envmod.unload_all(ctx.client, getattr(ctx, "baseline", None) or {}, timeout_s=30.0)
        except Exception:
            pass
        try:
            from bench import report as reportmod
            reportmod.write_report(run_dir)
        except Exception as e:  # noqa: BLE001
            with open(os.path.join(run_dir, "report_error.txt"), "w",
                       encoding="utf-8") as f:
                f.write(f"report failed: {e}\n{traceback.format_exc()[-2000:]}")
        envmod.set_thread_execution_state(False)
    if report_error:
        print(f"runner finished with error: {report_error[:300]}", file=sys.stderr)
        return 1
    return 0


def _case_key(ctx: Ctx, tag: str, profile: Profile, test_id: str, meta: dict,
              case: Case) -> str:
    return storemod.make_key(ctx.args.run_id, tag,
                             ctx.digest_by_tag.get(tag, "unknown")[:12],
                             test_id, meta.get("version", "n1"), case.id, 0,
                             meta.get("mode", "R0"),
                             profile.profile_id or tag)


def eligible_tests_for_fake(elig: dict, tag: str, test_ids: list[str]):
    ok, other = [], {}
    for tid in test_ids:
        info = (elig.get(tid, {}) or {}).get(tag)
        if info and info.get("code") == "E":
            ok.append(tid)
        else:
            other[tid] = info or {"code": "U", "reason": "no entry"}
    return ok, other


if __name__ == "__main__":
    raise SystemExit(main())
