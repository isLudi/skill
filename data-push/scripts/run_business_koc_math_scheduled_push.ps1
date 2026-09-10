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
$pushRuntime = 'C:\Users\Ludim\.codex\runtime\channel-broadcast-push\business-koc-math\scheduled'
New-Item -ItemType Directory -Path $pushRuntime -Force | Out-Null
$pushStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$pushOut = Join-Path $pushRuntime ("run-{0}-{1}.out.log" -f $pushStamp, $PID)
$pushErr = Join-Path $pushRuntime ("run-{0}-{1}.err.log" -f $pushStamp, $PID)
$pushArguments = @('-u', ('"{0}"' -f $pushScheduler), '--config', ('"{0}"' -f $pushConfig))
if ($Preflight) { $pushArguments += '--preflight' }
else { $pushArguments += @('--watch', '--confirm-send') }
$pushProcess = Start-Process -FilePath $pushPython -ArgumentList $pushArguments -WorkingDirectory (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -WindowStyle Hidden -RedirectStandardOutput $pushOut -RedirectStandardError $pushErr -PassThru -Wait
exit $pushProcess.ExitCode
