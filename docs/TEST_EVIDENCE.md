# Test evidence

Recorded for packaging remediation. This file reports one pytest invocation.
It does not claim a green run.

## Source

- Repository: `kot0070/local-llm-benchmark`
- Full commit: `9c3ffa05fd0162b79c0b86cf18ea4679eb4868eb`
- Commit timestamp: `2026-09-22 18:26:58 -0500` (`2026-09-22T23:26:58Z`)
- Subject: Rebuild both reports as per-model deep analysis (12 sheets, EN + UK)
- Working tree at run time: that commit, before the packaging files in this change

## Command

From the repository root:

```text
python -m pytest -q tests
```

Interpreter used: `/tmp/bench-venv/bin/python` (venv created for this run).

- Start: `2026-09-24T00:31:39Z`
- End: `2026-09-24T00:32:03Z`
- pytest reported duration: 24.34s
- Exit code: 1

## Counts

`pytest -q` did not print a separate "collected" line. The summary line was:

```text
7 failed, 375 passed, 3 skipped in 24.34s
```

| Outcome | Count |
| --- | ---: |
| passed | 375 |
| failed | 7 |
| skipped | 3 |
| error | 0 |
| outcome total | 385 |

Static count at the same commit, not a pytest result: 30 `test_*.py` files under `tests/`, and 331 lines matching `^def test_`. The pytest item count is higher because several of those functions are parametrized (`tests/test_analysis_report.py`, `tests/test_uk_sheets_deep.py`, `tests/test_owner_summary.py`). `pytest -q` did not print skip node ids.

## Environment

- OS: Ubuntu 24.04.4 LTS, Linux 6.12.94+ x86_64
- CPython: 3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0]
- `python3.13` was not available from apt after `apt-get update` on this machine. README and `SPEC_NIGHT.md` name Python 3.13 as the original interpreter. This run did not use 3.13.
- `nvidia-smi`: not found
- Packages installed into the venv before the run: Pillow 12.3.0, openpyxl 3.1.5, pytest 9.1.1 (openpyxl also pulled et-xmlfile 2.0.0; pytest also pulled iniconfig, packaging, pluggy, Pygments)
- `jsonschema` was not installed. A scan of `*.py` imports in this tree finds `PIL` and `openpyxl` as third-party runtime imports and `pytest` in tests. No module imports `jsonschema`. `SPEC_NIGHT.md` says the original Windows interpreter had jsonschema installed.

## Failed node ids

From the `pytest -q` short summary and assertion lines:

- `tests/test_analysis_report.py::test_real_smoke3_exit_zero_readonly` — `AssertionError: results/SMOKE3 missing`
- `tests/test_build_excel_report.py::test_failure_quotes_verified_real_run` — `AssertionError: ('aya-expanse:8b', 'H03-007')` / `assert None is not None`
- `tests/test_build_excel_report_en.py::test_failure_quotes_verified_real_run` — same assertion as the Ukrainian workbook test above
- `tests/test_build_excel_report_en.py::test_no_ranked_with_zero_scored` — `assert 0 == 215`
- `tests/test_core_fix_a.py::test_langs_reach_profile` — `FileNotFoundError` for `D:\LOCAL_AI\BENCH_V5_NIGHT\config\profiles.json`
- `tests/test_core_report.py::test_eligibility_file_structure` — `os.path.exists` was false for `D:\LOCAL_AI\BENCH_V5_NIGHT\config\eligibility_night.json`
- `tests/test_owner_summary.py::test_language_note_above_english_bullets` — `assert (-1 != -1)` on `first_bullet`

## Worktree side effect

After the run, `git status` showed modifications to:

- `results/night_20260921-155146/NIGHT1_REPORT.xlsx`
- `results/night_20260921-155146/NIGHT1_REPORT_EN.xlsx`

Those two files were restored with `git checkout` and are not part of the packaging commit.
