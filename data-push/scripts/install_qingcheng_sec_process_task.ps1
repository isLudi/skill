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
$runner = Join-Path $PSScriptRoot 'run_qingcheng_sec_process.py'
$configPath = Join-Path $PSScriptRoot '..\config\departments\qingcheng\sec_process_batch.json'
$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$calendar = $config.business_calendar
if ($config.status -ne 'active' -or -not $config.schedule_enabled -or
    $config.windows_task_name -ne 'Codex-Lark-Qingcheng-SEC-Process-GroupPush' -or
    (@($calendar.process_weekdays) -join ',') -ne '1,2,3,4,5,6' -or
    (@($calendar.hours) -join ',') -ne '12,16,20' -or
    $calendar.minute -ne 20 -or $calendar.deadline_minute -ne 50 -or
    $calendar.retry_interval_minutes -ne 2 -or
    @($config.reports).Count -ne 5) {
    throw 'SEC batch schedule differs from the reviewed configuration'
}

$existing = Get-ScheduledTask -TaskName $config.windows_task_name -ErrorAction SilentlyContinue
if ($existing) {
    throw 'An SEC process task already exists; review it before replacing'
}

$service = New-Object -ComObject 'Schedule.Service'
$service.Connect()
$folder = $service.GetFolder('\')
$definition = $service.NewTask(0)
$definition.RegistrationInfo.Description = 'Qingcheng SEC process reports; five independently gated deliveries'
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
foreach ($hour in @(12, 16, 20)) {
    $trigger = $definition.Triggers.Create(3)
    $trigger.StartBoundary = $startDay.AddHours($hour).AddMinutes(20).ToString('yyyy-MM-ddTHH:mm:ss')
    $trigger.WeeksInterval = 1
    $trigger.DaysOfWeek = 125
    $trigger.Repetition.Interval = 'PT2M'
    $trigger.Repetition.Duration = 'PT31M'
    $trigger.Repetition.StopAtDurationEnd = $false
}
$action = $definition.Actions.Create(0)
$action.Path = $pythonExe
$action.Arguments = '-u "' + $runner + '" --confirm-send'
$action.WorkingDirectory = $codexHome

$null = $folder.RegisterTaskDefinition($config.windows_task_name, $definition, 2, $null, $null, 3, $null)
$registered = Get-ScheduledTask -TaskName $config.windows_task_name -ErrorAction Stop
if ($registered.State -eq 'Disabled' -or @($registered.Triggers).Count -ne 3 -or
    @($registered.Actions).Count -ne 1 -or
    $registered.Actions[0].Execute -ne $pythonExe) {
    throw 'Registered SEC process task differs from the reviewed configuration'
}
$registered | Select-Object TaskName, State,
    @{Name='Triggers';Expression={@($_.Triggers).Count}},
    @{Name='Action';Expression={$_.Actions[0].Execute}},
    @{Name='Arguments';Expression={$_.Actions[0].Arguments}}
