param([switch]$Preflight)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$usqlEnvCandidates = @(Get-ChildItem -LiteralPath 'D:\GAOTU' -Directory -Filter '19002_*' -ErrorAction Stop |
    ForEach-Object { Join-Path $_.FullName 'usql_api.env' } |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
if ($usqlEnvCandidates.Count -ne 1) { throw 'Expected exactly one 19002_*/usql_api.env under D:\GAOTU.' }
$env:USQL_ENV_FILE = $usqlEnvCandidates[0]
$pushPython = 'D:\anaconda3\python.exe'
$pushScheduler = Join-Path $PSScriptRoot 'scheduled_push.py'
$pushConfig = Join-Path (Split-Path $PSScriptRoot -Parent) 'config\supervisor_yafei_grade_9_advisor_scheduled_push.json'
$pushArguments = @('-u', $pushScheduler, '--config', $pushConfig)
if ($Preflight) { $pushArguments += '--preflight' }
else { $pushArguments += @('--watch', '--confirm-send') }
& $pushPython @pushArguments 2>&1 | Out-Null
exit $LASTEXITCODE
