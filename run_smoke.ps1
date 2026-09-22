# Smoke launcher: 2 cases/test on 6 models, 0.4 h budget.
param(
  [double]$BudgetHours = 0.4,
  [string]$RunId = "",
  [string]$Resume = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = "D:\LOCAL_AI\homefield-bench\.venv\Scripts\python.exe"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir "smoke_$Stamp.log"

if (-not $env:BENCH_OLLAMA_URL) { $env:BENCH_OLLAMA_URL = "http://127.0.0.1:11434" }
if ($RunId -eq "") {
  if ($Resume -ne "") { $RunId = $Resume }
  else { $RunId = "smoke_" + (Get-Date -Format "yyyyMMdd-HHmmss") }
}
$Models = "qwen3:1.7b,functiongemma:270m,nomic-embed-text:latest,granite3.2-vision:2b,reader-lm:1.5b,nuextract:3.8b"

"root=$Root run_id=$RunId budget_hours=$BudgetHours url=$env:BENCH_OLLAMA_URL" | Tee-Object -FilePath $Log -Append

& $Py (Join-Path $Root "tools\gen_all.py") --missing-only 2>&1 | Tee-Object -FilePath $Log -Append
if ($LASTEXITCODE -ne 0) { throw "gen_all failed" }

& $Py -m pytest -q tests 2>&1 | Tee-Object -FilePath $Log -Append
if ($LASTEXITCODE -ne 0) { throw "pytest failed, aborting smoke run" }

$runArgs = @("-m", "bench.runner", "--budget-hours", "$BudgetHours", "--run-id", $RunId, "--smoke", "--models", $Models)
if ($Resume -ne "") { $runArgs += @("--resume", $Resume) }
& $Py @runArgs 2>&1 | Tee-Object -FilePath $Log -Append
$runCode = $LASTEXITCODE

& $Py -m bench.report $RunId 2>&1 | Tee-Object -FilePath $Log -Append

"done run_id=$RunId runner_exit=$runCode log=$Log" | Tee-Object -FilePath $Log -Append
exit $runCode
