param([switch]$ConfirmEnable, [switch]$CreateDisabled)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
if (($ConfirmEnable -and $CreateDisabled) -or (-not $ConfirmEnable -and -not $CreateDisabled)) {
    throw 'Choose exactly one registration phase.'
}
if ((Get-TimeZone).Id -ne 'China Standard Time') { throw 'Beijing timezone is required.' }
$pushRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$pushSkill = Split-Path $PSScriptRoot -Parent
$pushMachine = Get-Content -LiteralPath (Join-Path $pushRoot 'machine.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$pushConfigPath = Join-Path $pushSkill 'config\departments\market_consultant\app_volume.json'
$pushConfig = Get-Content -LiteralPath $pushConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$pushPythonw = Join-Path (Split-Path $pushMachine.executables.python -Parent) 'pythonw.exe'
$pushEntry = Join-Path $PSScriptRoot 'channels\market_consultant\app_volume.py'
$pushArguments = '"{0}" run --confirm-send' -f $pushEntry
if ($pushConfig.channel_id -ne 'app_volume' -or $pushConfig.adapter -ne 'market-volume-v1') {
    throw 'APP volume identity mismatch.'
}
if ($ConfirmEnable -and -not $pushConfig.schedule.enabled) { throw 'Canonical APP volume schedule is paused.' }
$pushName = $pushConfig.schedule.windows_task_name
$pushExisting = Get-ScheduledTask -TaskName $pushName -ErrorAction SilentlyContinue
if ($pushExisting -and ($pushExisting.Actions[0].Execute -ne $pushPythonw -or $pushExisting.Actions[0].Arguments -ne $pushArguments)) {
    throw 'Existing task owner/action differs.'
}
$pushStart = [DateTimeOffset]::Parse($pushConfig.schedule.first_send_at).LocalDateTime
$pushTrigger = New-ScheduledTaskTrigger -Daily -At $pushStart
$pushAction = New-ScheduledTaskAction -Execute $pushPythonw -Argument $pushArguments -WorkingDirectory $pushRoot
$pushPrincipal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$pushSettingsArgs = @{Hidden=$true;MultipleInstances='IgnoreNew';ExecutionTimeLimit=(New-TimeSpan -Minutes 35);
    AllowStartIfOnBatteries=$true;DontStopIfGoingOnBatteries=$true}
if ($CreateDisabled) { $pushSettingsArgs.Disable = $true }
$pushSettings = New-ScheduledTaskSettingsSet @pushSettingsArgs
$pushRegistration = @{TaskName=$pushName;Action=$pushAction;Trigger=$pushTrigger;Principal=$pushPrincipal;Settings=$pushSettings;
    Description='APP volume progress daily at 17:20, retry every two minutes until 17:50. Independent ledger and target.'}
if ($pushExisting) { $pushRegistration.Force = $true }
Register-ScheduledTask @pushRegistration | Out-Null
$pushTask = Get-ScheduledTask -TaskName $pushName
$pushInfo = Get-ScheduledTaskInfo -TaskName $pushName
[pscustomobject]@{name=$pushName;enabled=$pushTask.Settings.Enabled;state=[string]$pushTask.State;
    next_run=$pushInfo.NextRunTime.ToString('o');execute=$pushTask.Actions[0].Execute;
    arguments=$pushTask.Actions[0].Arguments;start=$pushTask.Triggers[0].StartBoundary} | ConvertTo-Json -Compress
