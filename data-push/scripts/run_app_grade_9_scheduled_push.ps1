param([switch]$Preflight, [switch]$ProbeOnly)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
if ($Preflight -and $ProbeOnly) { throw 'Choose one no-send mode.' }
$pushRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$pushMachine = Get-Content -LiteralPath (Join-Path $pushRoot 'machine.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$pushPython = [string]$pushMachine.executables.python
if (-not (Test-Path -LiteralPath $pushPython -PathType Leaf)) { throw 'Configured Python is unavailable.' }
$env:USQL_ENV_FILE = [string]$pushMachine.credential_file_paths.usql_env
$pushConfig = Join-Path (Split-Path $PSScriptRoot -Parent) 'config\app_grade_9_scheduled_push.json'
if ($ProbeOnly) {
    $pushEntry = Join-Path $PSScriptRoot 'channels\market_consultant\app_grade_9.py'
    $pushArguments = @('-u', $pushEntry, 'preflight-now', '--request-id', 'grade9-background-probe-20261014')
} else {
    $pushEntry = Join-Path $PSScriptRoot 'scheduled_push.py'
    $pushArguments = @('-u', $pushEntry, '--config', $pushConfig)
    if ($Preflight) { $pushArguments += '--preflight' }
    else { $pushArguments += @('--watch', '--confirm-send') }
}
$pushLog = $null
try {
    $pushLogDirectory = Join-Path (Join-Path (Join-Path $pushMachine.paths.push_log_root 'market_consultant') 'app_grade_9') (Get-Date -Format 'yyyy-MM-dd')
    New-Item -ItemType Directory -Path $pushLogDirectory -Force | Out-Null
    $pushLog = Join-Path $pushLogDirectory ((Get-Date -Format 'HHmmss') + '-process.log')
} catch { Write-Warning 'Push process log is unavailable; delivery may continue.' }
if ($pushLog) {
    $pushEncoding = [System.Text.UTF8Encoding]::new($false)
    & $pushPython @pushArguments 2>&1 | ForEach-Object {
        [System.IO.File]::AppendAllText($pushLog, [string]$_ + [Environment]::NewLine, $pushEncoding)
    }
} else { & $pushPython @pushArguments 2>&1 | Out-Null }
exit $LASTEXITCODE
