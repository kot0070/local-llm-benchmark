# results/night2_b — consolidated 28-model run (index)

Run `night2_b`: 4 models imported from GGUF into Ollama (Q4_K_M), Ollama
0.34.3, 5-hour time box. The raw harness outputs (`results.jsonl`,
`results.csv`, `summary.md`) hold 1810 records: 1090 belong to the 4 NIGHT-2
models and 720 are out-of-scope rows for the 24 NIGHT-1 tags (mostly PERF
probes) written by a mistaken resume command without a model filter. Raw
records are never edited; both workbooks exclude those rows by model tag.

## Models and ratings

- `night2-qwen3-vl-8b:q4km`: 7.9
- `night2-qwen3.5-9b:q4km`: 7.7
- `night2-nomic-embed-code:q4km`: 7.6
- `night2-ministral-3-8b:q4km`: 6.4

Ratings use round(10*(0.7*mean_q_sem+0.3*ok_rate),1). No HOME test exists for
these models, so the formula has no home term and these ratings are NOT
comparable with NIGHT-1 ratings (0.5/0.3/0.2 formula with a home term). The
workbooks show them as a separate scorecard band.

## Coverage

Status mix over the 1810 raw records: OK 657, WRONG_ANSWER 108, FORMAT_ERROR
158, OUTPUT_TRUNCATED 32, CONTEXT_OVERFLOW 4, TIMEOUT 4,
UNSUPPORTED_CAPABILITY 609, NOT_RUN_BUDGET 238. 238 NIGHT-2 cases are
NOT_RUN_BUDGET (time box). A resume did not re-run them because of a harness
bug: three `done_keys` refreshes in `bench/runner.py` discarded the resume
filter. The bug is fixed in `refresh_done_keys`, with a regression test that
fails on the old code; those 238 cases have not been re-run since the fix.

## Files

- `NIGHT28_REPORT_EN.xlsx` — consolidated 28-model workbook in English, the
  primary deliverable: 12 sheets, 672 per-model test rows.
- `NIGHT28_REPORT.xlsx` — the same workbook in Ukrainian: 12 sheets, and every
  number agrees with the English edition.
- `summary.md` — machine-generated report: run overview, per-test ranking
  tables with Q_sem / Q_strict / coverage / confidence intervals, HOME
  verdicts, and the DEFERRED list.
- `results.jsonl` — raw per-record file (1810 records, never edited).
- `results.csv` — scored (model, test) table: 700 rows (28 models x 25 tests).
- `perf.csv` — per-model timing probes.
- `errors.csv` — errors table.
- `telemetry.csv` — per-sample telemetry.
- `manifest.json` — run identity: run id, budget, Ollama version, sha256 of
  every file under `bench/` `gen/` `config/`, fixture manifests, model
  digests, fingerprint, model order.
- `preflight.json` — preflight details.
- `models/` — per-model detail folder.

At publication, `python -m pytest -q tests` in the Windows development environment (CPython 3.13.15) reported 428 passed and 0 failed. This is a single-environment result; see `docs/TEST_EVIDENCE.md` for the cross-environment record.
