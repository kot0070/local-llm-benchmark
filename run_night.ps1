# NIGHT-1 launcher: fixtures -> selftest -> run -> report. Unattended-safe:
# native stderr never aborts the script (Windows PowerShell 5.1 turns it into errors),
# and a failing selftest is logged loudly but does not cancel the night.
param(
  [double]$BudgetHours = 8,
  [string]$RunId = "",
  [string]$Resume = "",
  [string]$Models = "",
  [string]$Tests = ""
)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = "D:\LOCAL_AI\homefield-bench\.venv\Scripts\python.exe"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir "night_$Stamp.log"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"
Set-Location $Root

function Log([string]$msg) {
  $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg
  Write-Host $line
  Add-Content -Path $Log -Value $line -Encoding UTF8
}

# Run python with stdout+stderr appended to the log (via cmd, so PowerShell never wraps stderr).
function RunPy([string[]]$PyArgs) {
  $quoted = ($PyArgs | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ } }) -join " "
  cmd.exe /c "`"$Py`" $quoted >> `"$Log`" 2>&1"
  return $LASTEXITCODE
}

if (-not $env:BENCH_OLLAMA_URL) { $env:BENCH_OLLAMA_URL = "http://127.0.0.1:11434" }
if ($RunId -eq "") {
  if ($Resume -ne "") { $RunId = $Resume }
  else { $RunId = "night_" + (Get-Date -Format "yyyyMMdd-HHmmss") }
}
Log "root=$Root run_id=$RunId budget_hours=$BudgetHours url=$env:BENCH_OLLAMA_URL log=$Log"

Log "== fixtures (missing only) =="
$c = RunPy @((Join-Path $Root "tools\gen_all.py"), "--missing-only")
if ($c -ne 0) { Log "FIXTURE GENERATION FAILED (exit $c) - aborting"; exit 2 }

Log "== selftest =="
$c = RunPy @("-m", "pytest", "-q", "-p", "no:cacheprovider", "tests")
if ($c -ne 0) { Log "WARNING: SELFTEST FAILED (exit $c) - continuing the run anyway; see log" }

Log "== run (live progress: results\$RunId\results.jsonl) =="
$runArgs = @("-m", "bench.runner", "--budget-hours", "$BudgetHours", "--run-id", $RunId)
if ($Resume -ne "") { $runArgs += @("--resume", $Resume) }
if ($Models -ne "") { $runArgs += @("--models", $Models) }
if ($Tests -ne "") { $runArgs += @("--tests", $Tests) }
$runCode = RunPy $runArgs
Log "runner exit=$runCode"

Log "== report =="
$c = RunPy @("-m", "bench.report", $RunId)
Log "report exit=$c"

Log "done run_id=$RunId runner_exit=$runCode summary=results\$RunId\summary.md"
exit $runCode
