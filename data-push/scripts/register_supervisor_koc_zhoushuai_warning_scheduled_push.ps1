param([switch]$ConfirmEnable, [switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
if (-not $ConfirmEnable -and -not $VerifyOnly) { throw 'Explicit ConfirmEnable is required for this new daily task.' }
$skillRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $skillRoot)
$configPath = Join-Path $skillRoot 'config/departments/market_consultant/supervisor_koc_zhoushuai_warning.json'
$cfg = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$machine = Get-Content -LiteralPath (Join-Path $workspaceRoot 'machine.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$pythonw = Join-Path (Split-Path -Parent $machine.executables.python) 'pythonw.exe'
$entry = Join-Path $PSScriptRoot 'channels/market_consultant/supervisor_koc_zhoushuai_warning.py'
if (-not (Test-Path -LiteralPath $pythonw) -or -not (Test-Path -LiteralPath $entry)) { throw 'Pinned Python or entrypoint missing.' }
if (-not $cfg.schedule.enabled -or $cfg.schedule.kind -ne 'daily_once') { throw 'Canonical daily schedule must be enabled first.' }
if ($cfg.schedule.hours.Count -ne 1 -or $cfg.schedule.hours[0] -ne 17 -or $cfg.schedule.prepare_minute -ne 45 -or $cfg.schedule.send_minute -ne 50) { throw 'Daily trigger policy drift.' }
$taskName = $cfg.schedule.windows_task_name
if (-not $VerifyOnly -and (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)) { throw 'Task already exists; review it instead of replacing it.' }
$firstSend = [DateTimeOffset]::Parse($cfg.schedule.first_send_at).LocalDateTime
$prepareAt = $firstSend.AddMinutes(-5)
if (-not $VerifyOnly -and $prepareAt -le [DateTime]::Now) { throw 'The first preparation trigger must remain in the future.' }
$expectedNext = $prepareAt
if ($VerifyOnly -and $expectedNext -le [DateTime]::Now) {
    $expectedNext = [DateTime]::Now.Date.AddHours(17).AddMinutes(45)
    if ($expectedNext -le [DateTime]::Now) { $expectedNext = $expectedNext.AddDays(1) }
}
$action = New-ScheduledTaskAction -Execute $pythonw -Argument ('"' + $entry + '" run --confirm-send') -WorkingDirectory $workspaceRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $prepareAt
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$settings.StartWhenAvailable = $false
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'KOC Zhoushuai: prepare 17:45, send once 17:50; Mon-Thu process, Fri-Sun conversion; first 2026-10-11.'
if (-not $VerifyOnly) { Register-ScheduledTask -TaskName $taskName -InputObject $task | Out-Null }
$installed = Get-ScheduledTask -TaskName $taskName
$info = Get-ScheduledTaskInfo -TaskName $taskName
$xml = (Export-ScheduledTask -TaskName $taskName).Replace('encoding="UTF-16"', 'encoding="UTF-8"')
$receipt = [ordered]@{
    task_name = $taskName; enabled = $installed.Settings.Enabled; state = [string]$installed.State
    next_run_time = $info.NextRunTime.ToString('yyyy-MM-dd HH:mm:ss')
    action_execute = $installed.Actions[0].Execute; action_arguments = $installed.Actions[0].Arguments
    start_boundary = $installed.Triggers[0].StartBoundary
    trigger_count = $installed.Triggers.Count; start_when_available = $installed.Settings.StartWhenAvailable
    multiple_instances = [string]$installed.Settings.MultipleInstances
    logon_type = [string]$installed.Principal.LogonType; manual_run_started = $false
}
$stateRoot = $cfg.state_dir
New-Item -ItemType Directory -Path $stateRoot -Force | Out-Null
[IO.File]::WriteAllText((Join-Path $stateRoot 'windows-task.xml'), $xml, [Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText((Join-Path $stateRoot 'windows-task-receipt.json'), ($receipt | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
if ($installed.Triggers.Count -ne 1 -or -not $installed.Settings.Enabled -or $installed.Settings.StartWhenAvailable -or $info.NextRunTime.ToString('yyyy-MM-dd HH:mm') -ne $expectedNext.ToString('yyyy-MM-dd HH:mm') -or $installed.Actions[0].Execute -ne $pythonw -or $installed.Actions[0].Arguments -ne $action.Arguments -or [DateTimeOffset]::Parse($installed.Triggers[0].StartBoundary).LocalDateTime -ne $prepareAt -or $installed.Principal.LogonType -ne 'Interactive' -or $installed.Settings.MultipleInstances -ne 'IgnoreNew') { throw 'Installed schedule readback differs from the reviewed daily task.' }
$receipt | ConvertTo-Json -Depth 8
