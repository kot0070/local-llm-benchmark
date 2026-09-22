# results/night_20260921-155146 — deliverable run (index)

Run `night_20260921-155146`: 24 models, 24 HOME tests plus the PERF probe
group, 4190 records, 8-hour time box. For narrative read `OWNER_SUMMARY_UK.md`
then `ANALYSIS_UK.md`; for numbers read `summary.md` then the CSV tables and
the workbook.

- `summary.md` — machine-generated report: run overview, per-test ranking
  tables with Q_sem / Q_strict / coverage / 95% bootstrap intervals, HOME
  verdicts, and the DEFERRED list.
- `OWNER_SUMMARY_UK.md` — owner-facing summary (Ukrainian): run overview, HOME
  verdicts per test, top-3 per test, per-model highlights.
- `ANALYSIS_UK.md` — per-model / per-test analysis (Ukrainian): factual
  behaviour notes grounded in the records, usage recommendations for this
  hardware class, short verbatim failure examples with case ids.
- `results.csv` — one row per scored (model, test) pair: counts, Q_sem,
  Q_strict, confidence bounds, coverage.
- `owner_tables.csv` — the full (model, test) score table behind the summary;
  the file to use for any re-plotting.
- `perf.csv` — per-model timing probes: cold load seconds, time to first
  token, prompt and generation throughput, offload share.
- `NIGHT1_REPORT.xlsx` — consolidated 12-sheet workbook (Ukrainian) built from this run
  (plus the gv follow-up): the same scored data in spreadsheet form.
- `NIGHT1_REPORT_EN.xlsx` — the same 12-sheet analysis in English, the primary
  artifact for US readers: every (model, test) pair and all 24 model ratings agree
  with the Ukrainian edition. Per-model depth lives in five sheets — the model
  scorecard with ratings (`Model Scorecard` / `Оцінка моделей`), recommendations
  (`Recommendations` / `Рекомендації`), strengths and weaknesses
  (`Strengths & Weaknesses` / `Сильні та слабкі сторони`), per-model test detail
  covering all 576 model-test pairs (`Per-Model Test Detail` / `Деталі по тестах`),
  and failure analysis (`Failure Analysis` / `Аналіз помилок`).
- `manifest.json` — run identity: run id, budget, sha256 of every file under
  `bench/` `gen/` `config/`, fixture manifests, model digests, fingerprint,
  model order.

Deliberately not tracked here: the raw per-record file (`results.jsonl`,
about 11 MB of full model outputs), per-sample telemetry, the errors table,
preflight details, per-model detail folder, and the duplicate spreadsheet
export (`owner_summary.xlsx`, same data as the CSV tables).

HOME-07 dual condition: the smallest vision model scored Q_sem 0.000 on its
HOME document test under the uniform structured-answer contract in this run.
A separate follow-up (`results/night_20260921-155146_gv/`, 16 cases under a
plain-answer variant: 15 wrong answers + 1 truncated, format clean) also
scored 0.000 — a genuine extraction limit of that model on this task, not a
format artefact. The two conditions must not be compared as one series; see
`../night_20260921-155146_gv/summary.md` and `manifest.json` for the
follow-up run identity.
