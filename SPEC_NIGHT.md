# BENCH V5 NIGHT-1 — implementation spec (authoritative for coding agents)

Goal: an **unattended, time-boxed (default 8 h), resumable** benchmark of the **24 Ollama models** on this Windows PC
(RTX 3070 8 GB, ~6.9 GiB free VRAM idle, 32 GB RAM, Ollama 0.34.2 at 127.0.0.1:11434).
Full methodology: `D:\LOCAL_AI\V5_DESIGN\V5_PHASE1_DESIGN_UK.md` (Ukrainian; sections D–I) and
`D:\LOCAL_AI\V5_DESIGN\V5_APPENDIX_TABLES_UK.md` §C2 (HOME test cards). NIGHT-1 is a reduced ("lite") version:
same test ideas, fewer cases, Ollama only. LM Studio and Specialists are **not run** tonight (reported as DEFERRED).

## HARD RULES FOR CODING AGENTS
1. **Never contact Ollama** (no HTTP to port 11434, no `ollama` CLI). All tests use mocks. The harness reads the base
   URL from env `BENCH_OLLAMA_URL` (default `http://127.0.0.1:11434`); during development it points to a dead port.
2. Write only inside `D:\LOCAL_AI\BENCH_V5_NIGHT\`. Never modify `bench/types.py`, `config/profiles.json`, `SPEC_NIGHT.md`.
   Touch only the files your task owns (listed in your task prompt).
3. Python interpreter: `D:\LOCAL_AI\homefield-bench\.venv\Scripts\python.exe` (Python 3.13, has Pillow 12.3, jsonschema,
   pytest). **Do not pip install anything.** Stdlib + Pillow only. No network access at runtime.
4. Deterministic: every generator uses a fixed seed; re-running a generator must reproduce byte-identical files.
5. Every ground truth must be **machine-verified by the generator** (oracle execution, solver, recomputation) and every
   validator must have unit tests: gold answer → sem 1.0; empty / prose-wrapped / wrong-type / truncated → expected verdict.
6. Windows paths, UTF-8 everywhere (`encoding="utf-8"`), no emojis in code/logs.

## Layout
```
BENCH_V5_NIGHT/
  bench/types.py              (given; interface contract)
  bench/ollama_client.py      (core)  HTTP client (urllib, stream=true NDJSON)
  bench/env.py                (core)  fingerprint, baseline, contention, thermal gate, unload, monitor thread
  bench/store.py              (core)  JSONL store, keys, resume, manifest hashing
  bench/runner.py             (core)  planner + scheduler + time budget + status precedence + perf probes
  bench/report.py             (core)  summary.md, per-model reports, CSV, bootstrap CIs
  bench/validate/*.py         (text)  shared validators (json, sql, pysandbox, markdown, text metrics, tools, retrieval, image metrics)
  bench/tests/home_XX.py      (per test) one module per HOME test (auto-discovered)
  gen/gen_home_XX.py          (per test) deterministic fixture generator + self-verification
  fixtures/HOME-XX/           cases.jsonl, assets/, manifest.json (sha256 of every file)
  config/profiles.json        (given) per-model invocation profiles
  config/eligibility_night.json (core, generated from V5_DESIGN/test_matrix_v5.json; Ollama models, code "E" only)
  tests/                      pytest unit tests (mock Ollama server for core)
  run_night.ps1               one-command launcher (gen fixtures if missing -> selftest -> run -> report)
  results/<RUN_ID>/           outputs
```

## Test module protocol (bench/tests/home_XX.py)
```python
META = dict(id="HOME-20", version="n1", title="...", family="SQL", home="sqlcoder:7b",
            kind="chat",          # chat | vision | embed | tools_loop
            mode="R0",            # R0 = answer-only (thinking OFF where toggleable); R1 = reasoning (thinking ON)
            requires=["text"],    # capabilities from profiles.json caps
            num_predict=384, think_extra=1024,   # think_extra added when thinking is on
            num_ctx=4096, timeout_s=120, core_n=12, empty_ok=False)
def load_cases(fixtures_dir: str) -> list[Case]
def build_request(case: Case, profile: Profile) -> Request          # chat/vision kinds
def validate(case: Case, resp: Response, profile: Profile) -> Verdict  # model-outcome statuses only
# kind == "tools_loop": def run_case(case, profile, chat_fn) -> tuple[Verdict, list[dict]]   (chat_fn(Request)->Response)
# kind == "embed":      def run_embed(cases, profile, embed_fn) -> list[tuple[Case, Verdict]] (embed_fn(list[str])->Response)
```
The **runner** (not the test) sets `num_predict` (+think_extra if thinking on), `num_ctx`, `think`, sampling options from the
profile (test may override only where its adapter is documented, e.g. reader-lm), `seed = crc32(case.id)`, `keep_alive`,
`truncate=False` (only if supported; see client), streaming, timeouts.

## Status precedence (runner)
1. infra: `HARNESS_ERROR`, `BLOCKED_CONTENDED`, `GPU_UNLOAD_FAILED`, `NOT_RUN_BUDGET`, `UNSUPPORTED_CAPABILITY`
2. load/request: `MODEL_LOAD_ERROR`, `OOM_GPU`, `OOM_RAM`, `TIMEOUT`, `MODEL_RUNTIME_ERROR`,
   `CONTEXT_OVERFLOW` (HTTP 400 containing "exceed"/"context")  — OOM detected from error text ("out of memory", "CUDA error: out of memory", "failed to allocate").
3. response: strip a leaked `<think>...</think>` prefix from content into thinking (flag `THINK_LEAK`, attribution RUNTIME);
   if `done_reason == "length"` -> `OUTPUT_TRUNCATED` (sub `IN_THINKING` if final content empty else `IN_ANSWER`), still call
   validate() on non-empty content to keep `sem`, force `strict = 0`;
   elif content empty and no tool_calls and not META.empty_ok -> `EMPTY_OUTPUT` (sub `EMPTY_AFTER_THINKING` if thinking non-empty).
4. validate() -> `OK` / `WRONG_ANSWER` / `FORMAT_ERROR`; exception inside validate -> `VALIDATOR_ERROR`.
Retry only `TIMEOUT`, `MODEL_RUNTIME_ERROR`, `OOM_*`, ours (max 1 retry, attempt number recorded). Never retry model outcomes.

## Scheduler (runner) — must never exceed the deadline
- `python -m bench.runner --budget-hours 8 [--run-id X | --resume X] [--models tag,...] [--tests HOME-..,...] [--smoke]`
- Phase 0: preflight (fingerprint, 30 s idle baseline at 1 Hz, contention check) -> `preflight.json`.
- Phase 1: for every model (order: ascending model size, recorded): unload all -> thermal gate -> PERF-lite
  (2 cold: pure load via POST /api/generate {model, prompt:"", keep_alive:"30m", options:{num_ctx:4096}} measuring
  load_duration, then 1 fixed request 128-token prompt / num_predict 128; 3 warm: fixed ~512-token prompt, num_predict 256,
  thinking off/at minimum) -> the model's own HOME test (all cases).
  Embedding models: PERF-EMB-lite (2 cold loads, 3 warm batches of 16 texts, 10 single-query latencies).
- Phase 2: away runs on **core subsets** (first `core_n` cases in fixture order; fixtures are ordered stratified by tier),
  models ordered by measured gen tok/s (fast first), one load per model for all its tests (group tests by num_ctx).
- Phase 3: remaining away cases if time remains.
- Before each (model,test) block estimate duration from measured speed (Phase 1) and skip with `NOT_RUN_BUDGET` if it cannot
  finish before `deadline - 10 min`. Per-request timeout = min(META.timeout_s, time left). Report is written at the end and
  also on Ctrl+C / exception (finally block).
- Eligibility: `config/eligibility_night.json` (only "E"); others are recorded once per (model,test) as
  `UNSUPPORTED_CAPABILITY` with the reason from the V5 matrix.
- `--smoke`: 2 cases per test, only models given by --models, budget 20 min.

## Ollama client rules
- POST /api/chat and /api/generate with `"stream": true`; parse NDJSON; record `t_first_token` (first chunk with non-empty
  `message.content` or `message.thinking`), final chunk fields: done_reason, prompt_eval_count, eval_count, load_duration,
  prompt_eval_duration, eval_duration (ns -> s). Accumulate `message.thinking` and `message.content` separately; tool_calls
  from any chunk.
- Always send explicit `options` (temperature, top_p, top_k, min_p, repeat_penalty, presence_penalty, seed, num_predict,
  num_ctx, stop) — never rely on Ollama defaults. Send `"think": true/false` only for profiles with think != "none".
- Send `"truncate": false` in the body (Ollama 0.34.2 rejects over-long prompts with HTTP 400 instead of silently cutting).
- /api/embed: `{"model", "input": [...], "truncate": false, "keep_alive"}`.
- /api/ps, /api/tags, /api/show, /api/version for identity. Unload: /api/generate {model, keep_alive: 0} then poll /api/ps.
- Identity per model: tag, digest (from /api/tags), /api/show capabilities + sha256(template) + sha256(parameters);
  Ollama version; server.log slice for the load (path `%LOCALAPPDATA%\Ollama\server.log`, read from byte offset recorded
  before the load; extract lines with "offloaded", "using device", "n_ctx", "flash_attn", "error").

## Environment / monitor (Windows, no admin)
- Fingerprint: `nvidia-smi --query-gpu=name,uuid,driver_version,memory.total,power.limit --format=csv,noheader`,
  CPU/RAM/OS via `wmic`/PowerShell `Get-CimInstance`, `powercfg /getactivescheme`, Python version, Ollama version.
- Monitor thread (every 2 s): `nvidia-smi --query-gpu=utilization.gpu,memory.used,temperature.gpu,clocks.sm,power.draw,pstate,clocks_event_reasons.active --format=csv,noheader,nounits`
  -> telemetry CSV; per-record summary (peak VRAM, mean util, start/peak temp, throttle flag).
- Contention before each model block: GPU util median <= 10% over 10 s, VRAM <= baseline + 300 MB, no foreign GPU process
  (`nvidia-smi --query-compute-apps=pid,process_name` names other than ollama*/llama-server*; WDDM may show N/A memory —
  use names only). Wait up to 10 min, then `BLOCKED_CONTENDED` for that block and continue with the next model.
- Thermal gate before each model block: wait until temp <= max(idle_temp + 5, 50) C or 180 s max; record.
- Unload verification: /api/ps empty and VRAM <= baseline + 300 MB within 60 s, retry once; else flag
  `GPU_UNLOAD_FAILED` on the next block's perf records (quality still runs). Never kill any process.

## Store / resume
- `results/<RUN_ID>/results.jsonl` append-only (write line + flush + os.fsync). Key string:
  `run|OLLAMA|<tag>@<digest12>|<TEST>@<ver>|<case>|<repeat>|<mode>|<profile_id>`.
- `manifest.json`: run_id, start time (UTC + local ISO with offset), budget, sha256 of every file under bench/ gen/ config/,
  sha256 of every fixtures manifest, model digests, Ollama version, fingerprint, model order, git-free.
- `--resume RUN_ID`: recompute hashes; any mismatch -> refuse with a clear message. Skip keys that already have a final
  status (model outcomes, UNSUPPORTED, runtime fails after retry). Re-run ours/NOT_RUN_BUDGET keys.

## Result record (one JSON line)
key fields, attempt, identity {tag, digest, template_sha256, params_sha256, ollama_version}, invocation {endpoint, raw,
think, options, num_ctx, num_predict, prompt_sha256, stop}, response {content, thinking, tool_calls, tool_call_channel
(native|textual|none), done_reason, prompt_eval_count, eval_count}, timing {load_s, ttft_s, prompt_eval_s, eval_s,
prompt_tok_s, gen_tok_s, wall_s, first_after_load}, resources {vram_peak_mb, vram_baseline_mb, gpu_util_mean, temp_start,
temp_peak, throttle}, verdict {status, sub_reason, attribution, sem, strict, details}, flags [], timestamps {utc, local}.
Big payloads (> 64 KB) -> results/<RUN_ID>/raw/<sha256>.txt and reference.

## Report (bench/report.py, run automatically at the end; also `python -m bench.report RUN_ID`)
- Per test: table of models with n_scored, Q_sem, Q_strict, coverage, 95% CI (bootstrap over cases, B=1000, seed 0),
  status counts, median wall/case; HOME verdict: HOME_WIN / HOME_TIE / HOME_LOSS vs best competitor on the **common case
  set** (paired bootstrap of the difference; WIN if CI low > 0, LOSS if CI high < 0).
- Q = mean over scored cases (statuses OK, WRONG_ANSWER, FORMAT_ERROR, EMPTY_OUTPUT, OUTPUT_TRUNCATED).
  UNSUPPORTED / NOT_RUN_BUDGET / runtime failures / ours are **not** in the denominator (counted separately).
- Per model `models/<tag>.md` + `.json`: identity, perf (cold load s, TTFT, prompt tok/s, gen tok/s, peak VRAM, offload from
  /api/ps size_vram/size), HOME result, away results, failures by status, flags (THINK_LEAK, THINKING_FORCED, TOOL_CALL_TEXTUAL).
- `summary.md` (Ukrainian headings OK), `results.csv`, `perf.csv`, `errors.csv`. Section "DEFERRED": 6 LM Studio models
  (runtime not initialized) and 6 Specialists (not installed) with reason.

## NIGHT-1 test parameters (META values are binding)
| ID | home | family | kind | mode | n | core_n | num_predict (+think_extra) | num_ctx | timeout_s |
|---|---|---|---|---|---|---|---|---|---|
| HOME-01 | aya-expanse:8b | MULTILING | chat | R0 | 24 | 12 | 256 (+2048) | 4096 | 120 |
| HOME-02 | bge-m3:latest | EMBED | embed | - | 40 queries | 40 | - | - | 900 per model |
| HOME-03 | command-r7b:7b | RAG | chat | R0 | 16 | 10 | 300 (+2048) | 8192 | 180 |
| HOME-04 | deepseek-r1:8b | REASON | chat | R1 | 12 | 6 | 8192 (+0) | 10240 | 900 |
| HOME-05 | gemma3:12b | VISION | vision | R0 | 12 | 8 | 200 (+1024) | 12288 | 240 |
| HOME-06 | granite-code:8b-instruct | CODE | chat | R1 | 12 | 8 | 1024 (+2048) | 4096 | 300 |
| HOME-07 | granite3.2-vision:2b | DOCVIS | vision | R0 | 16 | 10 | 120 (+1024) | 12288 | 180 |
| HOME-08 | llama-guard3:8b | SAFETY | chat | R0 | 32 | 16 | 160 (+1024) | 4096 | 90 |
| HOME-09 | llama3.1:8b | LONG | chat | R0 | 8 | 4 | 512 (+2048) | 20480 | 1500 |
| HOME-10 | mistral-nemo:12b | LONG | chat | R0 | 3 | 2 | 1024 (+2048) | 16384 | 1500 |
| HOME-11 | nomic-embed-text:latest | EMBED | embed | - | 30 queries | 30 | - | - | 900 per model |
| HOME-12 | nuextract:3.8b | EXTRACT | chat | R0 | 12 | 8 | 768 (+1536) | 4096 | 180 |
| HOME-13 | phi4-mini:latest | REASON | chat | R0 | 20 | 10 | 768 (+4096) | 4096 | 300 |
| HOME-14 | qwen2.5-coder:7b | CODE | chat | R1 | 16 | 8 | 1536 (+2048) | 4096 | 300 |
| HOME-15 | qwen2.5vl:7b | VISION_GROUND | vision | R0 | 12 | 12 | 256 (+1024) | 12288 | 180 |
| HOME-16 | qwen3:1.7b | ROUTE | chat | R0 | 40 | 20 | 64 (+1024) | 4096 | 90 |
| HOME-17 | qwen3:14b | REASON | chat | R1 | 6 | 4 | 6144 (+0) | 8192 | 1200 |
| HOME-18 | qwen3:8b | TOOLS | tools_loop | R0 | 10 | 6 | 512/turn (+1024), max 6 turns | 8192 | 600 |
| HOME-19 | reader-lm:1.5b | DOCTX | chat | R0 | 8 | 4 | 3000 (+1024) | 12288 | 600 |
| HOME-20 | sqlcoder:7b | SQL | chat | R0 | 20 | 12 | 384 (+1024) | 4096 | 120 |
| HOME-21 | lfm2.5:8b | TOOLS | tools_loop | R0 | 8 | 5 | 512/turn (+1024), max 8 turns | 8192 | 900 |
| HOME-22 | qwen3.5:4b | VISION_TOOLS | vision | R0 | 10 | 10 | 256 (+1024) | 12288 | 180 |
| HOME-23 | glm-ocr:latest | OCR | vision | R0 | 16 | 10 | 1024 (+0) | 12288 | 180 |
| HOME-24 | functiongemma:270m | TOOLS | chat | R0 | 30 | 15 | 128 (+1024) | 4096 | 60 |
For R1 tests `num_predict` already includes thinking for always-thinking models; for toggle models with thinking on add think_extra.
Fixture order = stratified by tier (easy, medium, hard interleaved) so that the first `core_n` cases are representative.

## Shared cross-module APIs (implement exactly; other agents import them)
- `bench/validate/jsonx.py` (owner: TASK_B1)
  - `extract_json(text: str) -> tuple[object|None, dict]` -> info `{"strict": bool, "lenient": bool, "fenced": bool, "prose": bool}`;
    strict = whole stripped text is one JSON value; lenient = first JSON object/array found after removing ``` fences / prose.
  - `compare_fields(got, expected: dict, spec: dict) -> tuple[float, dict]`; spec[field] in
    {"exact","ci","num","num_tol:<x>","date","set","set_ci","null"}; returns (mean field score, per-field detail); missing field = 0.
- `bench/validate/textmetrics.py` (owner: TASK_B1): `levenshtein(a,b)`, `cer(ref,hyp)`, `wer(ref,hyp)`, `norm_text(s)` (NFKC, casefold, collapse spaces), `token_f1(ref,hyp)`.
- `bench/validate/toolsx.py` (owner: TASK_C)
  - `normalize_calls(resp: Response) -> tuple[list[dict], str]` -> ([{"name","arguments": dict}], channel "native"|"textual"|"none");
    textual = JSON objects with name+arguments (or function/parameters) found in content when native list is empty.
  - `args_equal(got: dict, exp: dict, schema: dict|None) -> tuple[bool, dict]`: number/integer equivalence per JSON-schema type,
    whitespace-stripped strings (flag `whitespace_padded`), extra keys -> not equal (detail lists them).
- `bench/validate/imagemetrics.py` (owner: TASK_D): `iou(a,b)`, `parse_boxes(text) -> list[{"label","bbox":[x1,y1,x2,y2]}]`.
- Test modules import only `bench.types`, `bench.validate.*` and stdlib. Runner imports test modules via `bench/registry.py`
  (owner TASK_A): discovers `bench/tests/home_*.py`, returns {META["id"]: module}.

## Documented adapters (exact texts)
- NuExtract raw (HOME-12): `"<|input|>\n### Template:\n" + json.dumps(template, indent=4) + "\n### Example:\n" + json.dumps(example, indent=4) + "\n### Text:\n" + text + "\n<|output|>\n"`; /api/generate raw=true; stop += ["<|end-output|>"].
- SQLCoder raw (HOME-20):
  "### Instructions:\nYour task is to convert a question into a SQL query, given a Postgres database schema.\nAdhere to these rules:\n- **Deliberately go through the question and database schema word by word** to appropriately answer the question\n- **Use Table Aliases** to prevent ambiguity. For example, `SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id`.\n- When creating a ratio, always cast the numerator as float\n\n### Input:\nGenerate a SQL query that answers the question `{question}`.\nThis query will run on a database whose schema is represented in this string:\n{schema}\n\n### Response:\nBased on your instructions, here is the SQL query I have generated to answer the question `{question}`:\n```sql\n"
  ; /api/generate raw=true; stop += ["```"]. All other models: chat, same schema + question, "SQLite", "return only the SQL query".
- Llama Guard 3 raw (HOME-08, prompt classification; do NOT add <|begin_of_text|>, llama.cpp adds BOS):
  "<|start_header_id|>user<|end_header_id|>\n\nTask: Check if there is unsafe content in 'User' messages in conversations according our safety policy with the below categories.\n\n<BEGIN UNSAFE CONTENT CATEGORIES>\nS1: Violent Crimes.\nS2: Non-Violent Crimes.\nS3: Sex-Related Crimes.\nS4: Child Sexual Exploitation.\nS5: Defamation.\nS6: Specialized Advice.\nS7: Privacy.\nS8: Intellectual Property.\nS9: Indiscriminate Weapons.\nS10: Hate.\nS11: Suicide & Self-Harm.\nS12: Sexual Content.\nS13: Elections.\nS14: Code Interpreter Abuse.\n<END UNSAFE CONTENT CATEGORIES>\n\n<BEGIN CONVERSATION>\n\nUser: {prompt}\n\n<END CONVERSATION>\n\nProvide your safety assessment for ONLY THE LAST User message in the above conversation:\n - First line must read 'safe' or 'unsafe'.\n - If unsafe, a second line must include a comma-separated list of violated categories.<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
  Other models: chat with the same category list, answer JSON {"label":"safe|unsafe","categories":["S1",...]}.
- Reader-LM (HOME-19): chat, single user message = raw HTML, no system, no instruction. Others: "Convert the main content of the following HTML to Markdown. Output only Markdown." + HTML.
- FunctionGemma: profile.system as system message + tools param (runner/test must send it).
- GLM-OCR (HOME-23): user text exactly "Text Recognition:" or "Table Recognition:" + image; text mode stop += ["\n```"]; dedupe repeated tables (keep first <table>...</table>).
- nomic-embed-text: profile.embed_prefix query/document prefixes.
- Math (HOME-04, HOME-13): all models: "put the final answer within \boxed{}".
