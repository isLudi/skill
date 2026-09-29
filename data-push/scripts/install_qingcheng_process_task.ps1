$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

$codexHome = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$machine = Get-Content -LiteralPath (Join-Path $codexHome 'machine.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$pythonExe = $machine.executables.python
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw 'Configured Python executable is missing'
}
$runner = Join-Path $PSScriptRoot 'run_qingcheng_process.py'
$batchConfig = Join-Path $PSScriptRoot '..\config\departments\qingcheng\process_batch_preview.json'
$batch = Get-Content -LiteralPath $batchConfig -Raw -Encoding UTF8 | ConvertFrom-Json
if ($batch.status -ne 'active' -or -not $batch.schedule_enabled -or
    $batch.windows_task_name -ne 'Codex-Lark-Qingcheng-Process-GroupPush' -or
    $batch.retry_interval_minutes -ne 2 -or
    @($batch.business_calendar.process_weekdays) -join ',' -ne '1,2,3' -or
    @($batch.business_calendar.hours) -join ',' -ne '14,18,22' -or
    $batch.business_calendar.minute -ne 25 -or $batch.business_calendar.deadline_minute -ne 50) {
    throw 'Qingcheng batch schedule differs from the reviewed configuration'
}

$service = New-Object -ComObject 'Schedule.Service'
$service.Connect()
$folder = $service.GetFolder('\')
$definition = $service.NewTask(0)
$definition.RegistrationInfo.Description = 'Qingcheng three-channel process reports; six isolated groups'
$definition.Principal.UserId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$definition.Principal.LogonType = 3
$definition.Principal.RunLevel = 0
$definition.Settings.Enabled = $true
$definition.Settings.Hidden = $true
$definition.Settings.StartWhenAvailable = $false
$definition.Settings.DisallowStartIfOnBatteries = $false
$definition.Settings.StopIfGoingOnBatteries = $false
$definition.Settings.MultipleInstances = 2
$definition.Settings.ExecutionTimeLimit = 'PT40M'

$startDay = (Get-Date).Date.AddDays(1)
foreach ($hour in @(14, 18, 22)) {
    $trigger = $definition.Triggers.Create(3)
    $trigger.StartBoundary = $startDay.AddHours($hour).AddMinutes(25).ToString('yyyy-MM-ddTHH:mm:ss')
    $trigger.WeeksInterval = 1
    $trigger.DaysOfWeek = 28
    $trigger.Repetition.Interval = 'PT2M'
    $trigger.Repetition.Duration = 'PT26M'
    $trigger.Repetition.StopAtDurationEnd = $false
}
$action = $definition.Actions.Create(0)
$action.Path = $pythonExe
$action.Arguments = '-u "' + $runner + '" --confirm-send'
$action.WorkingDirectory = $codexHome

$existing = Get-ScheduledTask -TaskName $batch.windows_task_name -ErrorAction SilentlyContinue
if ($existing) {
    throw 'A Qingcheng process task already exists; review it before replacing'
}
$null = $folder.RegisterTaskDefinition($batch.windows_task_name, $definition, 2, $null, $null, 3, $null)
$registered = Get-ScheduledTask -TaskName $batch.windows_task_name -ErrorAction Stop
if ($registered.State -eq 'Disabled' -or @($registered.Triggers).Count -ne 3 -or @($registered.Actions).Count -ne 1) {
    throw 'Registered task readback differs'
}
$registered | Select-Object TaskName, State, @{Name='Triggers';Expression={@($_.Triggers).Count}},
    @{Name='Action';Expression={$_.Actions[0].Execute}}, @{Name='Arguments';Expression={$_.Actions[0].Arguments}}
