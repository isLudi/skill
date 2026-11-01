param([switch]$ConfirmEnable)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8';$env:PYTHONUTF8='1'
[Console]::InputEncoding=[System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
$OutputEncoding=[Console]::OutputEncoding
if(-not $ConfirmEnable){throw 'Explicit ConfirmEnable is required.'}
if((Get-TimeZone).Id -ne 'China Standard Time'){throw 'Beijing timezone is required.'}
$pushRoot=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$pushSkill=Split-Path $PSScriptRoot -Parent
$pushConfig=Get-Content -LiteralPath (Join-Path $pushSkill 'config/departments/market_consultant/supervisor_chenruichun.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if($pushConfig.adapter -ne 'market-chenruichun-daily-v1' -or -not $pushConfig.schedule.enabled -or ($pushConfig.schedule.hours -join ',') -ne '14,19') {throw 'Restored Chen configuration drift.'}
$pushMachine=Get-Content -LiteralPath (Join-Path $pushRoot 'machine.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$pushPythonw=Join-Path (Split-Path $pushMachine.executables.python -Parent) 'pythonw.exe'
$pushEntry=Join-Path $PSScriptRoot 'channels/market_consultant/supervisor_chenruichun.py'
$pushName='Codex-Lark-Supervisor-Chen-Ruichun-Push'
if(Get-ScheduledTask -TaskName $pushName -ErrorAction SilentlyContinue){throw 'Task exists; inspect before replacing.'}
$pushFirst=[DateTimeOffset]::Parse($pushConfig.schedule.first_send_at).LocalDateTime
$pushTriggers=foreach($pushHour in $pushConfig.schedule.hours){
    $pushAt=$pushFirst.Date.AddHours($pushHour)
    if($pushAt -lt $pushFirst){$pushAt=$pushAt.AddDays(1)}
    New-ScheduledTaskTrigger -Daily -At $pushAt
}
$pushArgs='"{0}" run --confirm-send' -f $pushEntry
$pushAction=New-ScheduledTaskAction -Execute $pushPythonw -Argument $pushArgs -WorkingDirectory $pushRoot
$pushPrincipal=New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$pushSettings=New-ScheduledTaskSettingsSet -Hidden -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 55) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $pushName -Action $pushAction -Trigger $pushTriggers -Principal $pushPrincipal -Settings $pushSettings -Description 'Chen Ruichun IP advisor report. Daily 14:00/19:00; Mon-Thu process, Fri-Sun conversion; contains all Chen Ruichun channels; post leads >5; no historical catch-up.' | Out-Null
$pushTask=Get-ScheduledTask -TaskName $pushName
$pushInfo=$pushTask | Get-ScheduledTaskInfo
[pscustomobject]@{name=$pushName;enabled=$pushTask.Settings.Enabled;state=[string]$pushTask.State;next_run=$pushInfo.NextRunTime.ToString('s');
    execute=$pushTask.Actions[0].Execute;arguments=$pushTask.Actions[0].Arguments;hidden=$pushTask.Settings.Hidden;
    start_when_available=$pushTask.Settings.StartWhenAvailable;logon_type=[string]$pushTask.Principal.LogonType;
    triggers=@($pushTask.Triggers | ForEach-Object {$_.StartBoundary})} | ConvertTo-Json -Depth 4
