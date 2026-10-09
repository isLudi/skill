param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('process', 'partner', 'special', 'transformation', 'dept')]
    [string]$Kind
)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

# Schedule-only maintenance: retain existing actions, settings and principal.
# Never start tasks, unregister existing tasks or enable a paused task.
$codexHome = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$configDir = Join-Path $PSScriptRoot '..\config\departments\qingcheng'
$files = @{
    process = 'process_batch_preview.json'; partner = 'partner_process_batch.json'
    special = 'special_process_batch.json'; transformation = 'transformation_batch.json'
    dept = 'transformation_batch.json'
}
$runners = @{
    process = 'run_qingcheng_process.py'; partner = 'run_qingcheng_partner_process.py'
    special = 'run_qingcheng_special_process.py'; transformation = 'run_qingcheng_transformation.py'
    dept = 'run_qingcheng_transformation.py'
}
$batch = Get-Content -LiteralPath (Join-Path $configDir $files[$Kind]) -Raw -Encoding UTF8 | ConvertFrom-Json
$schedule = if ($Kind -eq 'dept') { $batch.dept_schedule } else { $batch }
$cal = $schedule.business_calendar
if ($schedule.status -ne 'active' -or -not $schedule.schedule_enabled -or $cal.timezone -ne 'Asia/Shanghai') {
    throw 'Schedule must be explicitly active with the reviewed timezone'
}
$conversion = $Kind -in @('transformation', 'dept')
$hours = if ($Kind -in @('special', 'dept')) { @(13) } else { @(13, 17, 21) }
$minute = if ($Kind -eq 'transformation') { 52 } else { 50 }
$window = if ($conversion) { 53 } else { 50 }
$retry = if ($Kind -in @('special', 'partner')) { $cal.retry_interval_minutes } else { $batch.retry_interval_minutes }
if ($retry -ne 2 -or $cal.minute -ne $minute -or $cal.retry_window_minutes -ne $window) {
    throw 'Retry window differs from the reviewed schedule'
}
if ($conversion) {
    if ((@($cal.result_weekdays) -join ',') -ne '4,5,6,0') { throw 'Conversion weekdays differ' }
    foreach ($day in @('4', '5', '6', '0')) {
        if ((@($cal.hours_by_weekday.$day) -join ',') -ne ($hours -join ',')) { throw 'Conversion hours differ' }
    }
    $days = @('Friday', 'Saturday', 'Sunday', 'Monday')
} else {
    if ((@($cal.process_weekdays) -join ',') -ne '1,2,3' -or
        (@($cal.hours) -join ',') -ne ($hours -join ',')) { throw 'Process calendar differs' }
    $days = @('Tuesday', 'Wednesday', 'Thursday')
}
$machine = Get-Content -LiteralPath (Join-Path $codexHome 'machine.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$pythonExe = $machine.executables.python
$pythonwExe = $pythonExe -replace 'python\.exe$', 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonwExe -PathType Leaf)) { throw 'Configured hidden Python is missing' }
$runner = Join-Path $PSScriptRoot $runners[$Kind]
& $pythonExe $runner --check-config | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Runner rejected the configuration' }
$arguments = '-u "' + $runner + '"'
if ($Kind -eq 'dept') { $arguments += ' --audience dept' }
$arguments += ' --confirm-send'
$taskName = $schedule.windows_task_name
$expectedNames = @{
    process = 'Codex-Lark-Qingcheng-Process-GroupPush'
    partner = 'Codex-Lark-Qingcheng-Partner-Process-GroupPush'
    special = 'Codex-Lark-Qingcheng-Special-Process-GroupPush'
    transformation = 'Codex-Lark-Qingcheng-Transformation-GroupPush'
    dept = 'Codex-Lark-Qingcheng-Special-Transformation-GroupPush'
}
if ($taskName -ne $expectedNames[$Kind]) { throw 'Task identity differs' }
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    if ($existing.State -eq 'Disabled' -or @($existing.Actions).Count -ne 1 -or
        $existing.Actions[0].Execute -ne $pythonwExe -or
        $existing.Actions[0].Arguments -ne $arguments -or
        $existing.Actions[0].WorkingDirectory -ne $codexHome) {
        throw 'Existing task is paused or its action differs; no mutation performed'
    }
}
$repetition = (New-ScheduledTaskTrigger -Once -At '2026-01-01T00:00' `
    -RepetitionInterval (New-TimeSpan -Minutes 2) `
    -RepetitionDuration (New-TimeSpan -Minutes $window)).Repetition
$triggers = @()
foreach ($hour in $hours) {
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $days `
        -At ('2026-10-08T{0:d2}:{1:d2}:00' -f $hour, $minute)
    $trigger.Repetition = $repetition
    $triggers += $trigger
}
if ($existing) {
    Set-ScheduledTask -TaskName $taskName -TaskPath $existing.TaskPath -Trigger $triggers | Out-Null
} else {
    $action = New-ScheduledTaskAction -Execute $pythonwExe -Argument $arguments -WorkingDirectory $codexHome
    $principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
        -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -Hidden -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -MultipleInstances Parallel -ExecutionTimeLimit (New-TimeSpan -Minutes 40) -StartWhenAvailable:$false
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers `
        -Principal $principal -Settings $settings -Description 'Qingcheng isolated channel-special conversion reports' | Out-Null
}
$registered = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
if ($registered.State -eq 'Disabled' -or @($registered.Triggers).Count -ne $hours.Count -or
    $registered.Actions[0].Execute -ne $pythonwExe -or $registered.Actions[0].Arguments -ne $arguments) {
    throw 'Registered task readback differs'
}
[ordered]@{ TaskName = $taskName; State = [string]$registered.State;
    Triggers = @($registered.Triggers).Count; Arguments = $registered.Actions[0].Arguments } | ConvertTo-Json -Compress
