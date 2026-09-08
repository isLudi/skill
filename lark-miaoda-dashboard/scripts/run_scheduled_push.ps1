param([switch]$Preflight)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$pushPython = 'D:\anaconda3\python.exe'
$pushScript = Join-Path $PSScriptRoot 'scheduled_push.py'
$pushRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pushRuntime = Join-Path (Split-Path $pushRoot -Parent) 'runtime\channel-broadcast-push\scheduled'
New-Item -ItemType Directory -Path $pushRuntime -Force | Out-Null
$pushStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$pushOut = Join-Path $pushRuntime ("run-{0}-{1}.out.log" -f $pushStamp, $PID)
$pushErr = Join-Path $pushRuntime ("run-{0}-{1}.err.log" -f $pushStamp, $PID)
$pushArguments = @('-u', ('"{0}"' -f $pushScript))
if ($Preflight) { $pushArguments += '--preflight' }
else { $pushArguments += @('--watch', '--confirm-send') }
$pushProcess = Start-Process -FilePath $pushPython -ArgumentList $pushArguments -WorkingDirectory (Split-Path $pushRoot -Parent) -WindowStyle Hidden -RedirectStandardOutput $pushOut -RedirectStandardError $pushErr -PassThru -Wait
exit $pushProcess.ExitCode
