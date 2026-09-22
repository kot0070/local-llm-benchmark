# NIGHT-1 local-LLM benchmark (Ollama, 24 models, one 8-hour run)

An independent benchmark harness for local language models, built from scratch:
deterministic fixture generation, one validator module per test, a time-boxed
unattended runner with GPU handling, paired-bootstrap scoring, and generated
reports. The one completed run covered 24 Ollama models in a single 8-hour
evening session, producing 4190 result records across 24 HOME tests plus a PERF
timing probe group.

## Why this exists

This repository is a portfolio and methodology piece demonstrating benchmark
design and harness engineering: how to define tasks with machine-checkable
ground truth, run models fairly under a hard time budget on modest hardware,
and report numbers with their uncertainty stated. It is not a definitive model
leaderboard. Every timing-sensitive figure is hardware-specific, the away-test
matrix is incomplete by construction (see Limits), and there was exactly one
run with no repeats.

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
- `bench/env.py` — host fingerprinting (GPU identity, CPU/RAM description,
  active power scheme, Python and Ollama versions), a 2-second GPU monitor
  thread (utilisation, VRAM, temperature, throttle flags) feeding per-record
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
  normalisation, argument comparison), `imagemetrics.py` (box IoU and box
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
- `tests/` — pytest suite, 26 files, 251 tests green: validator unit tests
  (gold answer scores 1.0; empty, prose-wrapped, wrong, and truncated inputs
  map to their expected verdicts), core client/env/store/runner/report tests
  against a mock server, and per-family HOME validator tests. Run with the
  project interpreter: `python -m pytest -q tests`.
- `tools/` — reporting and export scripts, standard library only:
  `owner_summary.py` (owner-facing summary plus score tables),
  `analysis_report.py` (per-model/per-test behaviour analysis with verbatim
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
- `results/` — run outputs. The deliverable run is
  `results/night_20260921-155146/` (see its README for the file index);
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
utilisation, temperature), and the validator verdict with evidence.

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

Start at [`results/night_20260921-155146/README.md`](results/night_20260921-155146/README.md),
the index of the deliverable run folder. Headline numbers for run
`night_20260921-155146`: 24 models, 24 HOME tests plus the PERF probe group,
4190 records. Status mix: OK 1755, WRONG_ANSWER 576, FORMAT_ERROR 459,
OUTPUT_TRUNCATED 191, CONTEXT_OVERFLOW 4, UNSUPPORTED_CAPABILITY 406,
NOT_RUN_BUDGET 799 (about 19% of the planned matrix did not fit the 8-hour
box). A small follow-up run (`night_20260921-155146_gv`, 23 records) re-tested
one vision model on its HOME document test under a plain-answer variant; the
folder README states the numbers and why the two conditions must not be
compared as one series.

## Running it yourself

- Full run (8 h, unattended, resumable; logs to `logs/night_*.log`):
  `powershell -NoProfile -ExecutionPolicy Bypass -File run_night.ps1 -BudgetHours 8`.
  Resume with `run_night.ps1 -BudgetHours <h> -Resume <run_id>`.
- Quick check: `run_smoke.ps1` runs 2 cases per test on 6 models under a
  0.4-hour budget.
- Self-test: `python -m pytest -q tests` (251 tests, must stay green). The
  night launcher runs fixture generation (missing only) and this self-test
  before the timed run.
- Requirements: Windows, Ollama with the model set pulled locally, Python 3.13
  with the standard library plus Pillow, jsonschema, and pytest, and a GPU
  with enough VRAM for at least the smaller models. Timings are
  hardware-specific: expect different absolute throughput on different cards
  even when the relative findings hold, and keep the GPU otherwise idle during
  a run since contention invalidates measurements.

## Limits

One machine, one run, no repeats. About one fifth of the away matrix is
`NOT_RUN_BUDGET`, so cross-model away comparisons are uneven by construction;
prefer the HOME-vs-best-competitor verdicts on shared case sets. Validators
are deliberately strict about format, so capable models can show low
`Q_strict` next to high `Q_sem` — that split is information, not noise. Some
behaviours are hardware artefacts (partial GPU offload on larger models at
8 GB VRAM, slower generation at long contexts) and are reported as such, not
as model rankings.

## License

License: to be decided by the repository owner.
