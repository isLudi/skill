param([switch]$ConfirmEnable, [switch]$CreateDisabled)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
if (($ConfirmEnable -and $CreateDisabled) -or (-not $ConfirmEnable -and -not $CreateDisabled)) {
    throw 'Choose exactly one deployment phase.'
}
if ((Get-TimeZone).Id -ne 'China Standard Time') { throw 'This task requires the Beijing timezone.' }
$pushRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$pushMachine = Get-Content -LiteralPath (Join-Path $pushRoot 'machine.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$pushPython = [string]$pushMachine.executables.python
$pushPythonWindowless = Join-Path (Split-Path $pushPython -Parent) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pushPythonWindowless -PathType Leaf)) { throw 'Windowless Python is unavailable.' }
$pushConfigPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'config\app_grade_9_scheduled_push.json'
$pushScheduler = Join-Path $PSScriptRoot 'scheduled_push.py'
$pushConfig = & $pushPython $pushScheduler --config $pushConfigPath --show-config | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Could not resolve the reviewed task configuration.' }
if ($pushConfig.channel_key -ne 'market_consultant/app_grade_9' -or $pushConfig.windows_task_name -ne 'Codex-Lark-App-Grade9-Push') {
    throw 'Task identity mismatch.'
}
if ($ConfirmEnable -and -not $pushConfig.enabled) { throw 'The canonical schedule must be enabled first.' }
$pushTaskName = $pushConfig.windows_task_name
$pushHiddenLauncher = Join-Path $PSScriptRoot 'run_hidden_push.pyw'
$pushLauncher = Join-Path $PSScriptRoot 'run_app_grade_9_scheduled_push.ps1'
$pushArguments = '"{0}" "{1}"' -f $pushHiddenLauncher, $pushLauncher
$pushExisting = Get-ScheduledTask -TaskName $pushTaskName -ErrorAction SilentlyContinue
if ($pushExisting -and ($pushExisting.Actions[0].Arguments -ne $pushArguments -or $pushExisting.Actions[0].Execute -ne $pushPythonWindowless)) {
    throw 'Existing task has a different action; refusing overwrite.'
}
$pushAction = New-ScheduledTaskAction -Execute $pushPythonWindowless -Argument $pushArguments -WorkingDirectory $pushRoot
$pushTriggers = foreach ($pushHour in $pushConfig.hours) {
    New-ScheduledTaskTrigger -Daily -At ((Get-Date).Date.AddHours($pushHour).AddMinutes($pushConfig.prepare_minute))
}
$pushPrincipal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$pushSettingsArguments = @{Hidden=$true;MultipleInstances='IgnoreNew';ExecutionTimeLimit=(New-TimeSpan -Minutes 40);
    AllowStartIfOnBatteries=$true;DontStopIfGoingOnBatteries=$true;StartWhenAvailable=$true}
if ($CreateDisabled) { $pushSettingsArguments.Disable = $true }
$pushSettings = New-ScheduledTaskSettingsSet @pushSettingsArguments
$pushRegister = @{TaskName=$pushTaskName;Action=$pushAction;Trigger=$pushTriggers;Principal=$pushPrincipal;Settings=$pushSettings;
    Description='Grade 9 APP and Bilibili supervisor/advisor batch. 13:24/17:24/21:24; Mon-Thu current process; Fri-Sun current conversion and next process. Each message retries independently.'}
if ($pushExisting) { $pushRegister.Force = $true }
Register-ScheduledTask @pushRegister | Out-Null
$pushReadback = Get-ScheduledTask -TaskName $pushTaskName
$pushInfo = Get-ScheduledTaskInfo -TaskName $pushTaskName
[pscustomobject]@{TaskName=$pushTaskName;Enabled=$pushReadback.Settings.Enabled;State=$pushReadback.State.ToString();
    NextRunTime=$pushInfo.NextRunTime.ToString('s');Execute=$pushReadback.Actions[0].Execute;Arguments=$pushReadback.Actions[0].Arguments;
    WorkingDirectory=$pushReadback.Actions[0].WorkingDirectory;LogonType=$pushReadback.Principal.LogonType.ToString();
    Triggers=@($pushReadback.Triggers | ForEach-Object {[pscustomobject]@{StartBoundary=$_.StartBoundary;DaysInterval=$_.DaysInterval}})
} | ConvertTo-Json -Depth 5
