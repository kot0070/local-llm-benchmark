# Local-LLM benchmark (Ollama, 28 models across two runs)

## Portfolio snapshot

**Automated local-LLM evaluation framework built to run reproducible, machine-checkable tests under a fixed hardware and time budget.**

- **24 local models** evaluated across **24 HOME test families** plus performance probes.
- **4,190 result records** produced in one unattended 8-hour run.
- Deterministic fixture generation with self-verifying ground truth.
- Per-test validators for structured output, code, SQL, retrieval, tool calls, vision/document tasks, and text metrics.
- GPU/thermal monitoring, contention checks, model unload verification, resumable execution, and explicit failure taxonomy.
- Automated Markdown, CSV, JSON, and Excel reporting with paired-bootstrap confidence intervals.
- Engineering workflow used AI coding agents under task contracts, executable tests, raw-record review, and independent audit passes.

**Core stack:** Python · Ollama · pytest · JSONL · PowerShell · GPU telemetry · automated reporting

**What this demonstrates:** benchmark design, automation, LLM evaluation, reproducibility, error handling, statistical reporting, and agent-assisted engineering with verification rather than blind code generation.

Start with the completed run: [`results/night_20260921-155146/README.md`](results/night_20260921-155146/README.md).

---

An independent benchmark harness for local language models, built from scratch:
deterministic fixture generation, one validator module per test, a time-boxed
unattended runner with GPU handling, paired-bootstrap scoring, and generated
reports. Two runs are complete: NIGHT-1 covered 24 Ollama models in a single
8-hour evening session (4190 result records across 24 HOME tests plus a PERF
timing probe group, Ollama 0.34.2), and NIGHT-2 added 4 models imported from
GGUF into Ollama (1090 new records, Ollama 0.34.3). The headline deliverable is
the consolidated 28-model workbook pair in `results/night2_b/`:
`NIGHT28_REPORT_EN.xlsx` (English, primary) and `NIGHT28_REPORT.xlsx`
(Ukrainian); each has 12 sheets and 672 per-model test rows, and the two
editions agree on every number. The NIGHT-1 workbooks remain as the frozen
24-model snapshot of the first run.

## Why this exists

This repository is a portfolio and methodology piece demonstrating benchmark
design and harness engineering: how to define tasks with machine-checkable
ground truth, run models fairly under a hard time budget on modest hardware,
and report numbers with their uncertainty stated. It is not a definitive model
leaderboard. Every timing-sensitive figure is hardware-specific, the away-test
matrix is incomplete by construction (see Limits), and each run was a single
pass with no repeats.

## Architecture

- `bench/runner.py` — planner and scheduler. Loads per-model profiles and the
  eligibility matrix, orders models (ascending size for the HOME phase, fastest
  first for away phases), and walks each `(model, test)` block through unload,
  thermal gate, contention check, PERF-lite timing probe, and the test cases.
  Owns the time budget (skips blocks that cannot finish before deadline minus
  margin as `NOT_RUN_BUDGET`), the status precedence chain (infra, then
  load/request, then response-level, then validator verdict), one retry for
  retryable infra failures only, and append-only JSONL recording with resume
  keys. Module docstring: `python -m bench.runner --budget-hours 8
  [--run-id X | --resume X] [--models tag,...] [--tests HOME-..,...] [--smoke]`.
  A later fix corrected `--resume` handling in `refresh_done_keys` (mid-run
  `done_keys` refreshes had discarded the resume filter, so a resume did not
  re-run the 238 still-unrun NIGHT-2 cases), covered by a regression test that
  fails on the old code.
- `bench/env.py` — host fingerprinting (GPU identity, CPU/RAM description,
  active power scheme, Python and Ollama versions), a 2-second GPU monitor
  thread (utilization, VRAM, temperature, throttle flags) feeding per-record
  resource summaries, the pre-block contention check (median GPU util, VRAM
  headroom, foreign GPU-process names), the thermal gate, and unload
  verification. Never terminates foreign processes.
- `bench/ollama_client.py` — minimal Ollama HTTP client over urllib with
  `stream=true` NDJSON parsing. Records time to first token, token counts,
  load durations, and thinking/content channel separation. Always sends
  explicit sampling options; never relies on server defaults.
- `bench/store.py` — result store: append-only JSONL with flush+fsync, stable
  run keys (`run|OLLAMA|tag@digest|TEST@ver|case|repeat|mode|profile`), resume
  logic (skip final keys, re-run ours/unfinished), and sha256 manifest hashing.
- `bench/report.py` — post-run reporting: `summary.md` with per-test ranking
  tables, per-model `models/<tag>.md` + JSON detail, `results.csv`,
  `perf.csv`, `errors.csv`. Bootstrap confidence intervals (B=1000, seed 0).
- `bench/registry.py` — auto-discovers `bench/tests/home_*.py` and indexes
  modules by `META["id"]`.
- `bench/tests/home_XX.py` — one module per HOME test (24 files). Each declares
  a binding `META` record (id, version, title, family, home model, kind,
  reasoning mode, capability requirements, `num_predict`/`think_extra`,
  `num_ctx`, timeout, `core_n`) and implements `load_cases` / `build_request`
  / `validate` (plus `run_case` for tool-loop kinds and `run_embed` for
  embedding kinds). Validators return only model-outcome verdicts
  (`OK` / `WRONG_ANSWER` / `FORMAT_ERROR`); the runner handles everything
  infra- and response-level. Test modules import only `bench.types`,
  `bench.validate.*`, and the standard library.
- `bench/validate/` — shared validators: `jsonx.py` (strict vs lenient JSON
  extraction, per-field comparison), `textmetrics.py` (edit-distance and
  token-F1 text measures), `toolsx.py` (native vs textual tool-call
  normalization, argument comparison), `imagemetrics.py` (box IoU and box
  parsing), plus `sqlx.py`, `mdparse.py`, `pysandbox.py`, `retrieval.py`.
- `bench/types.py` — the interface contract (Case / Request / Response /
  Verdict dataclasses and status constants). Frozen by project rule.
- `gen/gen_home_XX.py` — one deterministic fixture generator per test (fixed
  seed, stratified easy/medium/hard case order so the first `core_n` cases are
  representative). Each writes `fixtures/HOME-XX/{cases.jsonl, assets/*,
  manifest.json}` and self-verifies its own ground truth (oracle execution,
  solver, or recomputation), raising on any inconsistency. Re-running a
  generator reproduces byte-identical files.
- `config/profiles.json` — per-model invocation profiles for all 24 models:
  kind, capability flags, thinking mode, context limit, sampling options,
  adapter flags, stop sequences, system prompts, and embed prefixes.
- `config/eligibility_night.json` — which `(model, test)` pairs run. Only code
  `E` pairs execute; the rest are recorded once as `UNSUPPORTED_CAPABILITY`
  with the design reason, never attempted.
- `tests/` — pytest suite, 30 `test_*.py` files (331 `def test_` at
  `9c3ffa05fd0162b79c0b86cf18ea4679eb4868eb`). On that commit
  (2026-09-22T23:26:58Z), `python -m pytest -q tests` reported 375 passed,
  7 failed, 3 skipped, and 0 errors (exit code 1; CPython 3.12.3,
  2026-09-24T00:31:39Z; see `docs/TEST_EVIDENCE.md`): validator unit tests
  (gold answer scores 1.0; empty, prose-wrapped, wrong, and truncated inputs
  map to their expected verdicts), core client/env/store/runner/report tests
  against a mock server, and per-family HOME validator tests. Run with the
  project interpreter: `python -m pytest -q tests`.
- `tools/` — reporting and export scripts (stdlib, plus openpyxl in the Excel builders):
  `owner_summary.py` (owner-facing summary plus score tables),
  `analysis_report.py` (per-model/per-test behavior analysis with verbatim
  failure examples), `build_excel_report.py` (consolidated `NIGHT1_REPORT.xlsx`
  workbook), `build_excel_report_en.py` (consolidated `NIGHT1_REPORT_EN.xlsx`
  workbook, the same analysis in English), `en_sheets_narrative.py` (per-model
  narrative sheets for the English workbook: scorecard, recommendations,
  strengths and weaknesses), `en_sheets_detail.py` (per-model detail sheets for
  the English workbook: test detail and failure analysis), `uk_sheets_deep.py`
  (the five deep per-model sheets for the Ukrainian workbook, mirroring the
  English ones), `gen_all.py` (run all fixture generators, `--missing-only`
  supported), `make_eligibility.py` (build the eligibility matrix from design
  sources).
- `results/` — run outputs. The headline deliverable is the consolidated
  28-model pair `results/night2_b/NIGHT28_REPORT_EN.xlsx` (English, primary)
  and `results/night2_b/NIGHT28_REPORT.xlsx` (Ukrainian), 12 sheets each (see
  `results/night2_b/README.md` for the run index).
  `results/night_20260921-155146/` holds the frozen NIGHT-1 24-model snapshot
  (see its README for the file index);
  `results/night_20260921-155146_gv/` holds the small follow-up condition for
  one vision model. `results/SMOKE*/` are intermediate development runs and
  are excluded from tracking.
- `run_night.ps1` / `run_smoke.ps1` — launchers. The night launcher generates
  missing fixtures only, runs the pytest self-test, executes the time-boxed
  runner under a chosen hour budget with a generated run id, and renders the
  report. The smoke launcher runs 2 cases per test on 6 models under a
  0.4-hour budget.

Representative reads used for this description: `SPEC_NIGHT.md` in full,
`bench/runner.py` (scheduler and status precedence), `bench/tests/home_20.py`
(text-to-SQL test module with its documented adapter branch),
`gen/gen_home_20.py` (seeded generator with machine-verified SQL ground
truth), both launcher scripts, and the run overviews in both result folders.

## Methodology

Each of the 24 HOME tests is designed around one model (its "HOME" model) and
run on that model with all cases; every other model takes a subset of other
tests ("away" tests), usually only the first `core_n` fixture cases so the
schedule fits the deadline. Before each block the harness unloads the previous
model, waits for the GPU to cool toward idle, checks for unrelated GPU load,
and records a short timing probe (cold loads, fixed prompts). Each block is
exception-guarded so one crash cannot end the run, and each record carries its
model identity (tag, digest, template/parameter hashes), invocation (endpoint,
options, prompt hash), response (content, thinking, tool calls, token counts),
timing (load, time to first token, throughput, wall), resources (VRAM peak,
utilization, temperature), and the validator verdict with evidence.

Outcome taxonomy:

- `OK` — the validator accepted the answer.
- `WRONG_ANSWER` — a well-formed answer with the wrong content.
- `FORMAT_ERROR` — the output contract was broken (prose around JSON, a fence
  where raw output was required, a textual tool call where a native call was
  required), but the content could still be scored leniently.
- `EMPTY_OUTPUT` / `OUTPUT_TRUNCATED` — response-level outcomes; truncation
  records whether generation stopped in the reasoning trace or in the answer.
- `UNSUPPORTED_CAPABILITY` — by design, not a failure: the pair was never
  attempted because the model lacks the needed capability (for example a
  text-only model on a vision test). Excluded from scoring, counted
  separately.
- `NOT_RUN_BUDGET` — not a model failure either: the scheduler skipped the
  block because it could not finish before the deadline minus a safety margin.
  Coverage below 1.0 usually reflects this time-boxing; by-design non-attempts
  (`UNSUPPORTED_CAPABILITY`) lower it too.
- `CONTEXT_OVERFLOW` and infra statuses (`TIMEOUT`, `HARNESS_ERROR`, and
  similar) — runtime outcomes, also outside the quality denominator.

Scoring: `Q_sem` (semantic quality, the ranking metric) is the mean score over
scored cases; `Q_strict` is the same score forced to 0 wherever the output
contract was broken, so a wide `Q_sem`/`Q_strict` gap means the model often
knew the answer but did not follow the format. Each test also carries a HOME
verdict — `HOME_WIN` / `HOME_TIE` / `HOME_LOSS` — comparing the HOME model
against its best competitor on the shared case set with a paired bootstrap;
low-coverage away rows are not ranked. Confidence intervals are 95%
bootstrap bands over cases (B=1000, seed 0); small tests have wide intervals
by nature.

## Engineering process

This project was built with an AI coding-agent workflow: a manager role wrote
per-task contracts, sub-agents implemented the code and analysis, and the
manager audited each step against the raw records before moving on. Several
rounds of live smoke testing caught and fixed real fairness and measurement
defects before the full run (for example a blocked-streaming read inflating
time-to-first-token, identical warm prompts inflating prompt throughput via
prefix caching, a chat path dropping stop sequences, and prompt templates that
showed contracts the validators did not actually enforce). The post-run
pipeline — generated analysis, an independent fresh-agent audit of that
analysis against the raw records, a fix step applying exactly the audit
findings, and a staged publish set the manager read file by file — is part of
the same discipline. That audit loop also once flagged apparent out-of-scope
file touches that, on direct re-investigation, traced to a pre-existing
integration test's intended side effect (the mandated full-suite pytest run
regenerates summary files for the smoke directories), and the record was
corrected in place. The episode is kept here because a process that flags,
investigates, and corrects its own findings is the point, not an embarrassment.

## Results

The headline deliverable is the consolidated 28-model workbook pair in
`results/night2_b/`: `NIGHT28_REPORT_EN.xlsx` (English, primary) and
`NIGHT28_REPORT.xlsx` (Ukrainian). Each workbook has 12 sheets and 672
per-model test rows covering all 28 measured models (24 from NIGHT-1 plus 4
from NIGHT-2); the English and Ukrainian editions agree on every number.
NIGHT-2 model ratings use round(10*(0.7*mean_q_sem+0.3*ok_rate),1) with no HOME
term, so they form a separate scorecard band and are not comparable with
NIGHT-1 ratings (0.5/0.3/0.2 formula with a home term): 7.9
(night2-qwen3-vl-8b:q4km), 7.7 (night2-qwen3.5-9b:q4km), 7.6
(night2-nomic-embed-code:q4km), 6.4 (night2-ministral-3-8b:q4km).

Start at [`results/night2_b/README.md`](results/night2_b/README.md) for the
consolidated run index, or at
[`results/night_20260921-155146/README.md`](results/night_20260921-155146/README.md),
the index of the NIGHT-1 run folder (the frozen 24-model snapshot). Headline
numbers for run `night_20260921-155146`: 24 models, 24 HOME tests plus the PERF
probe group, 4190 records, Ollama 0.34.2. Status mix: OK 1755, WRONG_ANSWER 576,
FORMAT_ERROR 459, OUTPUT_TRUNCATED 191, CONTEXT_OVERFLOW 4,
UNSUPPORTED_CAPABILITY 406, NOT_RUN_BUDGET 799 (about 19% of the planned matrix
did not fit the 8-hour box). Run `night2_b`: 4 models imported from GGUF into
Ollama, Ollama 0.34.3, 1810 raw records, of which 1090 belong to the 4 NIGHT-2
models and 720 are out-of-scope rows for the 24 NIGHT-1 tags (mostly PERF
probes) written by a mistaken resume command without a model filter; raw
records are never edited and the workbooks exclude those rows by model tag.
238 NIGHT-2 cases are NOT_RUN_BUDGET (time box) and have not been re-run since
the `--resume` fix noted above. A small follow-up run
(`night_20260921-155146_gv`, 23 records) re-tested one vision model on its HOME
document test under a plain-answer variant; the folder README states the
numbers and why the two conditions must not be compared as one series.

## Model scope

36 models were planned: 24 Ollama models, 6 LM Studio GGUF files, and 6
specialists. 28 are measured (24 from NIGHT-1 plus 4 NIGHT-2 imports); the rest
are excluded or pending for the reasons below.

| Group | Models | Status |
|---|---|---|
| NIGHT-1 Ollama set | 24 models in `night_20260921-155146` | Measured, 4190 records |
| NIGHT-2 imports (Q4_K_M) | night2-qwen3-vl-8b, night2-qwen3.5-9b, night2-nomic-embed-code, night2-ministral-3-8b | Measured, 1090 records |
| Too large for the 8 GB card, already quantized | Qwen3.5-35B-A3B (16 GB), Devstral-Small-2-24B (14 GB), gpt-oss-20b (12 GB) | Excluded |
| Phi-4-Multimodal | phi4mm support never merged into llama.cpp | Excluded |
| Nomic-Embed-Code | 28 GB FP32 build replaced by the official 4.08 GB Q4_K_M | Measured as night2-nomic-embed-code |
| Pending (need audio / reranking scoring paths the harness does not have) | DeepSeek-OCR, Qwen3-ASR-1.7B, BGE-Reranker-v2-m3, Kokoro-TTS | Not measured |

## Downstream use: local vs cloud routing test

These scores (RTX 3070 8 GB, Ollama) were later turned into a small capability and routing knowledge base: for each task type, which local model (if any) is reliable enough to use. The knowledge-base file itself is not published.

That knowledge base was then tested in practice in a private local-vs-cloud routing test. The hypothesis was that a manager/router which splits work between local models and cloud models can save cloud tokens. The test ran in a private n8n AI Workflow Router and its private PWA chat client (those repositories are not linked here). A Director → Manager → agents chain used local models as supervised helpers, chosen through the knowledge-base rules. The chain was driven by a prompt plus a master plan, not by a specialized agent framework.

Local-model calls: 21 in total, 20 of them agent-initiated. Phase 2: 4 calls on `qwen3:8b` (3 edited, 1 accepted). Phase 3: 7 calls (all edited).

Phase 3 also ran an A/B on one task class, N=2 per arm. The run labels the arms A and B. On the owner's account, A is the cloud-only arm (no local helper) and B is the local-helper arm, which is the slower one: billable tokens 57.9k vs 47.3k, cost $0.0079 vs $0.0077, wall time 98.6 s vs 180.3 s. Run-to-run noise was larger than the A/B gap.

On this hardware (8 GB GPU) and this task class, local AI did not produce reliable cloud-token savings, and arm B was slower. This must not be presented as a proven token-cost reduction. The sample is N=2 per arm and is indicative only.

## Running it yourself

- Full run (8 h, unattended, resumable; logs to `logs/night_*.log`):
  `powershell -NoProfile -ExecutionPolicy Bypass -File run_night.ps1 -BudgetHours 8`.
  Resume with `run_night.ps1 -BudgetHours <h> -Resume <run_id>`.
- Quick check: `run_smoke.ps1` runs 2 cases per test on 6 models under a
  0.4-hour budget.
- Self-test: `python -m pytest -q tests`. On commit
  `9c3ffa05fd0162b79c0b86cf18ea4679eb4868eb` (2026-09-22T23:26:58Z) that
  command reported 375 passed, 7 failed, 3 skipped, and 0 errors (exit code 1;
  see `docs/TEST_EVIDENCE.md`). The night launcher runs fixture generation
  (missing only) and this self-test before the timed run.
- Install, from the repository root: `pip install -e ".[dev]"` (Pillow,
  openpyxl, and pytest) or `pip install -r requirements.txt` and
  `pip install pytest`. Then `python -m pytest -q tests`.
- Requirements: Windows, Ollama with the model set pulled locally, Python 3.12
  or newer (`SPEC_NIGHT.md` records the original interpreter as Python 3.13;
  the evidence run used CPython 3.12.3), Pillow and openpyxl, pytest for the
  self-test, and a GPU with enough VRAM for at least the smaller models.
  Timings are hardware-specific: expect different absolute throughput on
  different cards even when the relative findings hold, and keep the GPU
  otherwise idle during a run since contention invalidates measurements.

## Limits

One machine, two runs, no repeats within a run. About one fifth of the away matrix is
`NOT_RUN_BUDGET`, so cross-model away comparisons are uneven by construction;
prefer the HOME-vs-best-competitor verdicts on shared case sets. Validators
are deliberately strict about format, so capable models can show low
`Q_strict` next to high `Q_sem` — that split is information, not noise. Some
behaviors are hardware artifacts (partial GPU offload on larger models at
8 GB VRAM, slower generation at long contexts) and are reported as such, not
as model rankings.

## License

License: to be decided by the repository owner.
