param([switch]$ConfirmEnable, [switch]$CreateDisabled)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
if (($ConfirmEnable -and $CreateDisabled) -or (-not $ConfirmEnable -and -not $CreateDisabled)) {
    throw 'Specify exactly one of -ConfirmEnable or -CreateDisabled.'
}
if ((Get-TimeZone).Id -ne 'China Standard Time') { throw 'Task host timezone must be China Standard Time.' }
$pushScheduler = Join-Path $PSScriptRoot 'scheduled_push.py'
$pushConfigPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'config\supervisor_zhu_doctor_video49_scheduled_push.json'
$pushConfig = & 'D:\anaconda3\python.exe' $pushScheduler --config $pushConfigPath --show-config | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Could not resolve the Zhu Doctor video49 schedule configuration.' }
if (-not $pushConfig.enabled -and $ConfirmEnable) { throw 'The registered channel schedule is disabled; review and authorize the channel configuration first.' }
$pushFirst = [DateTimeOffset]::Parse($pushConfig.first_send_at).LocalDateTime
$pushTaskName = 'Codex-Lark-Supervisor-Zhu-Doctor-Video49-Push'
$pushLauncher = Join-Path $PSScriptRoot 'run_supervisor_zhu_doctor_video49_scheduled_push.ps1'
$pushArguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $pushLauncher
$pushAction = New-ScheduledTaskAction -Execute "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument $pushArguments -WorkingDirectory (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent)
$pushExisting = Get-ScheduledTask -TaskName $pushTaskName -ErrorAction SilentlyContinue
if ($pushExisting -and $pushExisting.Actions.Arguments -ne $pushArguments) { throw 'Existing task has another action; refusing overwrite.' }
$pushTriggers = foreach ($pushHour in $pushConfig.hours) {
    $pushAt = $pushFirst.Date.AddHours($pushHour).AddMinutes($pushConfig.prepare_minute)
    if ($pushAt.AddMinutes(5) -lt $pushFirst) { $pushAt = $pushAt.AddDays(1) }
    New-ScheduledTaskTrigger -Daily -At $pushAt
}
$pushPrincipal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
if ($CreateDisabled -or -not $ConfirmEnable) {
    $pushSettings = New-ScheduledTaskSettingsSet -Disable -Hidden -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 40) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
} else {
    $pushSettings = New-ScheduledTaskSettingsSet -Hidden -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 40) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
}
$pushDescription = "data-push Zhu Doctor paired-minute advisor-grain broadcast; starts :$('{0:D2}' -f $pushConfig.prepare_minute), retries every 2 minutes through :50. Advisors with post leads below 1 are hidden and not mentioned."
$pushRegister = @{TaskName=$pushTaskName;Action=$pushAction;Trigger=$pushTriggers;Principal=$pushPrincipal;Settings=$pushSettings;Description=$pushDescription}
if ($pushExisting) { $pushRegister.Force = $true }
Register-ScheduledTask @pushRegister | Out-Null
$pushReadback = Get-ScheduledTask -TaskName $pushTaskName
$pushInfo = Get-ScheduledTaskInfo -TaskName $pushTaskName
[pscustomobject]@{TaskName=$pushTaskName;State=$pushReadback.State.ToString();NextRunTime=$pushInfo.NextRunTime;Triggers=@($pushReadback.Triggers | Select-Object StartBoundary,DaysInterval);Action=$pushReadback.Actions.Arguments;LogonType=$pushReadback.Principal.LogonType;MultipleInstances=$pushReadback.Settings.MultipleInstances;Enabled=$pushReadback.Settings.Enabled} | ConvertTo-Json -Depth 6
