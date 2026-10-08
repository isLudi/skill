$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

# ASCII-only on purpose: Windows PowerShell 5.1 reads BOM-less files as ANSI and
# non-ASCII comments corrupt parsing. Schedule source: operator records in Base
# table tbl3iMKvD52jaMF1 (9 supervisor/consultant + 4 dept records), windows
# adjusted 2026-10-01: Fri/Sat/Sun windows start at 14:02/18:02/22:02 (retry
# every 2 min until :55); next-Monday has a single 04:00 window so the
# 03:40 upstream batch can expose the 00:00 source partition.
# DaysOfWeek 97 = Fri32+Sat64+Sun1; DaysOfWeek 2 = Mon.
# 2026-10-02: dept level (four channels -> one shared group) joins this task by
# LEVELS in the run script; task registration stays identical to the other
# push tasks (pythonw.exe, Interactive, Hidden) per user confirmation.
# Uses Register-ScheduledTask cmdlets (the Schedule.Service COM object is
# unreliable in this host).

$codexHome = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$machine = Get-Content -LiteralPath (Join-Path $codexHome 'machine.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$pythonExe = $machine.executables.python -replace 'python\.exe$', 'pythonw.exe'  # hidden: no console window
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw 'Configured Python executable is missing'
}
$runner = Join-Path $PSScriptRoot 'run_qingcheng_transformation.py'
$batchConfig = Join-Path $PSScriptRoot '..\config\departments\qingcheng\transformation_batch.json'
$batch = Get-Content -LiteralPath $batchConfig -Raw -Encoding UTF8 | ConvertFrom-Json
$hours = $batch.business_calendar.hours_by_weekday
$minutes = $batch.business_calendar.minute_by_weekday
if ($batch.status -ne 'active' -or -not $batch.schedule_enabled -or
    $batch.windows_task_name -ne 'Codex-Lark-Qingcheng-Transformation-GroupPush' -or
    $batch.retry_interval_minutes -ne 2 -or
    @($batch.business_calendar.result_weekdays) -join ',' -ne '4,5,6,0' -or
    @($hours.'4') -join ',' -ne '14,18,22' -or
    @($hours.'5') -join ',' -ne '14,18,22' -or
    @($hours.'6') -join ',' -ne '14,18,22' -or
    @($hours.'0') -join ',' -ne '4' -or
    $batch.business_calendar.minute -ne 2 -or $batch.business_calendar.deadline_minute -ne 55 -or
    $minutes.'0' -ne 0 -or $minutes.'4' -ne 2 -or $minutes.'5' -ne 2 -or $minutes.'6' -ne 2) {
    throw 'Qingcheng transformation batch schedule differs from the reviewed configuration'
}

$taskName = $batch.windows_task_name
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    # Re-registration replaces the previous registration with the reviewed one.
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$repetition = (New-ScheduledTaskTrigger -Once -At '2026-01-01T00:00' `
    -RepetitionInterval (New-TimeSpan -Minutes 2) `
    -RepetitionDuration (New-TimeSpan -Minutes 54)).Repetition

$triggers = @()
foreach ($hour in @(14, 18, 22)) {
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday, Saturday, Sunday `
        -At ("2026-10-02T{0:d2}:02" -f $hour)
    $trigger.Repetition = $repetition
    $triggers += $trigger
}
$monday = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At '2026-10-05T04:00'
$monday.Repetition = $repetition
$triggers += $monday

$action = New-ScheduledTaskAction -Execute $pythonExe `
    -Argument ('-u "' + $runner + '" --confirm-send') `
    -WorkingDirectory $codexHome

$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive -RunLevel Limited

$settings = New-ScheduledTaskSettingsSet -Hidden `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances Parallel -ExecutionTimeLimit (New-TimeSpan -Minutes 40) `
    -StartWhenAvailable:$false

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers `
    -Principal $principal -Settings $settings -Description `
    'Qingcheng transformation reports; five channels, dept+supervisor+consultant levels, ten groups' | Out-Null

$registered = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
if ($registered.State -eq 'Disabled' -or @($registered.Triggers).Count -ne 4 -or @($registered.Actions).Count -ne 1) {
    throw 'Registered task readback differs'
}
$summary = [ordered]@{
    TaskName = $registered.TaskName
    State    = $registered.State
    Triggers = @($registered.Triggers).Count
    Action   = $registered.Actions[0].Execute
    Args     = $registered.Actions[0].Arguments
}
$summary | Format-List | Out-String
