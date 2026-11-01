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
$pushPythonw = Join-Path (Split-Path $pushMachine.executables.python -Parent) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pushPythonw -PathType Leaf)) { throw 'Configured pythonw is unavailable.' }
$pushIds = @('grade9_supervisor_bundle','localization_advisor_bundle','high_school_supervisor_bundle','douyin_advisor_bundle')
$pushResults = foreach ($pushId in $pushIds) {
    $pushConfigPath = Join-Path $pushSkill ('config\departments\market_consultant\' + $pushId + '.json')
    $pushConfig = Get-Content -LiteralPath $pushConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($pushConfig.channel_id -ne $pushId -or $pushConfig.domain -ne 'market_consultant' -or $pushConfig.adapter -ne 'market-grade-bundle-v2') {
        throw 'Registered bundle identity mismatch.'
    }
    if ($ConfirmEnable -and -not $pushConfig.schedule.enabled) { throw 'Canonical schedule is still paused.' }
    $pushEntry = Join-Path $PSScriptRoot ('channels\market_consultant\' + $pushId + '.py')
    $pushArguments = '"{0}" run --confirm-send' -f $pushEntry
    $pushName = $pushConfig.schedule.windows_task_name
    $pushExisting = Get-ScheduledTask -TaskName $pushName -ErrorAction SilentlyContinue
    if ($pushExisting -and ($pushExisting.Actions[0].Execute -ne $pushPythonw -or $pushExisting.Actions[0].Arguments -ne $pushArguments)) {
        throw 'An existing task has a different owner/action; refusing overwrite.'
    }
    $pushFirst = [DateTimeOffset]::Parse($pushConfig.schedule.first_send_at).LocalDateTime.Date
    $pushTriggers = foreach ($pushHour in $pushConfig.schedule.hours) {
        New-ScheduledTaskTrigger -Daily -At ($pushFirst.AddHours($pushHour))
    }
    $pushAction = New-ScheduledTaskAction -Execute $pushPythonw -Argument $pushArguments -WorkingDirectory $pushRoot
    $pushPrincipal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
    $pushSettingsArgs = @{Hidden=$true;MultipleInstances='IgnoreNew';ExecutionTimeLimit=(New-TimeSpan -Minutes 55);
        AllowStartIfOnBatteries=$true;DontStopIfGoingOnBatteries=$true}
    if ($CreateDisabled) { $pushSettingsArgs.Disable = $true }
    $pushSettings = New-ScheduledTaskSettingsSet @pushSettingsArgs
    $pushRegister = @{TaskName=$pushName;Action=$pushAction;Trigger=$pushTriggers;Principal=$pushPrincipal;Settings=$pushSettings;
        Description='Market grade-first group bundle: daily 14:00 and 19:00, Mon-Thu process / Fri-Sun conversion. Independent group/channel recovery; no historical catch-up.'}
    if ($pushExisting) { $pushRegister.Force = $true }
    Register-ScheduledTask @pushRegister | Out-Null
    $pushTask = Get-ScheduledTask -TaskName $pushName
    $pushInfo = Get-ScheduledTaskInfo -TaskName $pushName
    [pscustomobject]@{channel_id=$pushId;name=$pushName;enabled=$pushTask.Settings.Enabled;state=[string]$pushTask.State;
        next_run=$pushInfo.NextRunTime.ToString('s');execute=$pushTask.Actions[0].Execute;arguments=$pushTask.Actions[0].Arguments;
        working_directory=$pushTask.Actions[0].WorkingDirectory;hidden=$pushTask.Settings.Hidden;
        start_when_available=$pushTask.Settings.StartWhenAvailable;logon_type=[string]$pushTask.Principal.LogonType;
        triggers=@($pushTask.Triggers | ForEach-Object {[pscustomobject]@{start=$_.StartBoundary;daily_interval=$_.DaysInterval}})}
}
$pushResults | ConvertTo-Json -Depth 5
