param([switch]$Preflight)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$pushPython = 'D:\anaconda3\python.exe'
$pushScheduler = Join-Path $PSScriptRoot 'scheduled_push.py'
$pushConfig = Join-Path (Split-Path $PSScriptRoot -Parent) 'config\business_koc_math_scheduled_push.json'
$pushArguments = @('-u', $pushScheduler, '--config', $pushConfig)
if ($Preflight) { $pushArguments += '--preflight' }
else { $pushArguments += @('--watch', '--confirm-send') }
& $pushPython @pushArguments 2>&1 | Out-Null
exit $LASTEXITCODE
