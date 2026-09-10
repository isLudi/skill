param([switch]$ConfirmEnable)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
if (-not $ConfirmEnable) { throw 'Explicit -ConfirmEnable is required.' }
if ((Get-TimeZone).Id -ne 'China Standard Time') { throw 'Task host timezone must be China Standard Time.' }
$pushScheduler = Join-Path $PSScriptRoot 'scheduled_push.py'
$pushConfigPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'config\business_koc_math_scheduled_push.json'
$pushConfig = & 'D:\anaconda3\python.exe' $pushScheduler --config $pushConfigPath --show-config | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Could not resolve the business-KOC schedule configuration.' }
if (-not $pushConfig.enabled) { throw 'The registered channel schedule is disabled.' }
$pushFirst = [DateTimeOffset]::Parse($pushConfig.first_send_at).LocalDateTime
$pushTaskName = 'Codex-Lark-Business-KOC-Math-Push'
$pushLauncher = Join-Path $PSScriptRoot 'run_business_koc_math_scheduled_push.ps1'
$pushArguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $pushLauncher
$pushAction = New-ScheduledTaskAction -Execute "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument $pushArguments -WorkingDirectory (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent)
$pushExisting = Get-ScheduledTask -TaskName $pushTaskName -ErrorAction SilentlyContinue
if ($pushExisting) {
    if ($pushExisting.Actions.Arguments -ne $pushArguments) { throw 'Existing task has another action; refusing overwrite.' }
    throw 'Task already exists; inspect before explicitly updating it.'
}
$pushTriggers = foreach ($pushHour in $pushConfig.hours) {
    $pushAt = $pushFirst.Date.AddHours($pushHour).AddMinutes($pushConfig.prepare_minute)
    if ($pushAt.AddMinutes(5) -lt $pushFirst) { $pushAt = $pushAt.AddDays(1) }
    New-ScheduledTaskTrigger -Daily -At $pushAt
}
$pushPrincipal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$pushSettings = New-ScheduledTaskSettingsSet -Hidden -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 40) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$pushDescription = 'data-push business KOC math reports. Prepare 09:15/13:15/17:15/21:15; send :20-:50. Channels: KOC-Zhoushuai math, then KOC-Mengyafei math. Requires Windows login and network.'
Register-ScheduledTask -TaskName $pushTaskName -Action $pushAction -Trigger $pushTriggers -Principal $pushPrincipal -Settings $pushSettings -Description $pushDescription | Out-Null
$pushReadback = Get-ScheduledTask -TaskName $pushTaskName
$pushInfo = Get-ScheduledTaskInfo -TaskName $pushTaskName
[pscustomobject]@{TaskName=$pushTaskName;State=$pushReadback.State.ToString();NextRunTime=$pushInfo.NextRunTime;Triggers=@($pushReadback.Triggers | Select-Object StartBoundary,DaysInterval);Action=$pushReadback.Actions.Arguments;LogonType=$pushReadback.Principal.LogonType;MultipleInstances=$pushReadback.Settings.MultipleInstances;Enabled=$pushReadback.Settings.Enabled} | ConvertTo-Json -Depth 6
