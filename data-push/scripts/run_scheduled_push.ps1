param([switch]$Preflight)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$pushPython = 'D:\anaconda3\python.exe'
$pushScript = Join-Path $PSScriptRoot 'channels\market_consultant\self_incubated_koc_5.py'
$pushRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pushArguments = @('-u', $pushScript)
if ($Preflight) { $pushArguments += 'preflight' }
else { $pushArguments += @('run', '--confirm-send') }
& $pushPython @pushArguments 2>&1 | Out-Null
exit $LASTEXITCODE
