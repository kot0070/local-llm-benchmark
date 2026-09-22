"""Interface contract for BENCH V5 NIGHT-1. Do not modify (coding agents)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# ----------------------------------------------------------------- statuses
OK = "OK"
WRONG_ANSWER = "WRONG_ANSWER"
FORMAT_ERROR = "FORMAT_ERROR"
EMPTY_OUTPUT = "EMPTY_OUTPUT"
OUTPUT_TRUNCATED = "OUTPUT_TRUNCATED"
UNSUPPORTED_CAPABILITY = "UNSUPPORTED_CAPABILITY"
CONTEXT_OVERFLOW = "CONTEXT_OVERFLOW"
TIMEOUT = "TIMEOUT"
MODEL_LOAD_ERROR = "MODEL_LOAD_ERROR"
MODEL_RUNTIME_ERROR = "MODEL_RUNTIME_ERROR"
VALIDATOR_ERROR = "VALIDATOR_ERROR"
HARNESS_ERROR = "HARNESS_ERROR"
OOM_GPU = "OOM_GPU"
OOM_RAM = "OOM_RAM"
BLOCKED_CONTENDED = "BLOCKED_CONTENDED"
GPU_UNLOAD_FAILED = "GPU_UNLOAD_FAILED"
NOT_RUN_BUDGET = "NOT_RUN_BUDGET"
PARTIAL_CASE_ERROR = "PARTIAL_CASE_ERROR"

MODEL_OUTCOME = {OK, WRONG_ANSWER, FORMAT_ERROR, EMPTY_OUTPUT, OUTPUT_TRUNCATED}          # scored (in Q denominator)
RUNTIME_FAIL = {TIMEOUT, MODEL_LOAD_ERROR, MODEL_RUNTIME_ERROR, OOM_GPU, OOM_RAM, CONTEXT_OVERFLOW}
OURS = {HARNESS_ERROR, VALIDATOR_ERROR, BLOCKED_CONTENDED, GPU_UNLOAD_FAILED}
NOT_SCORED = {UNSUPPORTED_CAPABILITY, NOT_RUN_BUDGET}
RETRYABLE = RUNTIME_FAIL - {CONTEXT_OVERFLOW} | OURS

ATTRIBUTIONS = {"MODEL", "RUNTIME", "HARNESS", "VALIDATOR", "ENVIRONMENT", "POLICY", "NONE"}


@dataclass
class Case:
    id: str
    test_id: str
    tier: str = ""            # easy | medium | hard
    lang: str = "en"
    input: dict = field(default_factory=dict)
    expected: Any = None
    meta: dict = field(default_factory=dict)


@dataclass
class Profile:
    """One entry of config/profiles.json."""
    tag: str
    kind: str                 # chat | embed
    caps: list                # e.g. ["text","tools","vision","json_format","fim","embed"]
    think: str                # toggle | always | none
    ctx_max: int
    sampling: dict            # {"default": {...}, "thinking": {...}, "nonthinking": {...}}  (missing keys -> "default")
    adapters: dict = field(default_factory=dict)   # documented adapter flags, e.g. {"nuextract_raw": true}
    stop: list = field(default_factory=list)
    system: Optional[str] = None                    # documented system prompt (e.g. functiongemma activation)
    embed_prefix: dict = field(default_factory=dict)  # {"query": "...", "document": "..."}
    profile_id: str = ""
    notes: str = ""
    langs: list = field(default_factory=lambda: ["multi"])  # documented languages; "multi" = broad / not enumerated


@dataclass
class Request:
    endpoint: str                                   # chat | generate | embed
    messages: Optional[list] = None                 # chat: [{"role","content","images"?: [b64,...], "tool_calls"?...}]
    prompt: Optional[str] = None                    # generate
    raw: bool = False                               # generate raw=true (documented raw templates)
    tools: Optional[list] = None
    format: Any = None
    think: Optional[bool] = None                    # set by runner from profile + META.mode unless test sets it
    options: dict = field(default_factory=dict)     # test-level overrides (runner merges profile sampling first)
    embed_input: Optional[list] = None
    force_think: bool = False                       # test explicitly requires its own think value (rare)


@dataclass
class Response:
    content: str = ""
    thinking: str = ""
    tool_calls: list = field(default_factory=list)
    done_reason: Optional[str] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    load_s: Optional[float] = None
    prompt_eval_s: Optional[float] = None
    eval_s: Optional[float] = None
    ttft_s: Optional[float] = None
    wall_s: float = 0.0
    http_status: Optional[int] = None
    error: Optional[str] = None
    raw: dict = field(default_factory=dict)
    embeddings: Optional[list] = None


@dataclass
class Verdict:
    status: str
    sub_reason: Optional[str] = None
    sem: float = 0.0
    strict: float = 0.0
    details: dict = field(default_factory=dict)
    attribution: str = "NONE"
