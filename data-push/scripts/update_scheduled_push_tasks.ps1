param([switch]$ConfirmUpdate)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
if (-not $ConfirmUpdate) { throw 'Explicit -ConfirmUpdate is required.' }
if ((Get-TimeZone).Id -ne 'China Standard Time') { throw 'Task host timezone must be China Standard Time.' }

$pushDefinitions = @(
    @{ Config = 'scheduled_push.json'; Task = 'Codex-Lark-Market-KOC-GroupPush'; Launcher = 'run_scheduled_push.ps1' },
    @{ Config = 'business_koc_math_scheduled_push.json'; Task = 'Codex-Lark-Business-KOC-Math-Push'; Launcher = 'run_business_koc_math_scheduled_push.ps1' },
    @{ Config = 'supervisor_koc_douyin_sync_scheduled_push.json'; Task = 'Codex-Lark-Supervisor-KOC-Douyin-Push'; Launcher = 'run_supervisor_koc_douyin_sync_scheduled_push.ps1' },
    @{ Config = 'supervisor_private_app_sync_scheduled_push.json'; Task = 'Codex-Lark-Supervisor-Private-App-Push'; Launcher = 'run_supervisor_private_app_sync_scheduled_push.ps1' },
    @{ Config = 'supervisor_self_incubated_koc_5_grade_9_scheduled_push.json'; Task = 'Codex-Lark-Supervisor-KOC-Grade9-Push'; Launcher = 'run_supervisor_self_incubated_koc_5_grade_9_scheduled_push.ps1' },
    @{ Config = 'supervisor_yafei_grade_9_scheduled_push.json'; Task = 'Codex-Lark-Supervisor-Yafei-Grade9-Push'; Launcher = 'run_supervisor_yafei_grade_9_scheduled_push.ps1' },
    @{ Config = 'supervisor_zhu_doctor_video49_scheduled_push.json'; Task = 'Codex-Lark-Supervisor-Zhu-Doctor-Video49-Push'; Launcher = 'run_supervisor_zhu_doctor_video49_scheduled_push.ps1' },
    @{ Config = 'supervisor_chenruichun_scheduled_push.json'; Task = 'Codex-Lark-Supervisor-Chen-Ruichun-Push'; Launcher = 'run_supervisor_chenruichun_scheduled_push.ps1' }
)
$pushPlan = @()
foreach ($pushDefinition in $pushDefinitions) {
    $pushConfigPath = Join-Path (Split-Path $PSScriptRoot -Parent) ('config\' + $pushDefinition.Config)
    $pushConfig = & 'D:\anaconda3\python.exe' (Join-Path $PSScriptRoot 'scheduled_push.py') --config $pushConfigPath --show-config | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw "Could not resolve schedule for $($pushDefinition.Task)." }
    if ($pushConfig.windows_task_name -ne $pushDefinition.Task) { throw "Config/task mismatch for $($pushDefinition.Task)." }
    $pushTask = Get-ScheduledTask -TaskName $pushDefinition.Task -ErrorAction Stop
    $pushExpectedLauncher = Join-Path $PSScriptRoot $pushDefinition.Launcher
    if ($pushTask.Actions.Count -ne 1 -or $pushTask.Actions.Arguments -notlike "*$pushExpectedLauncher*") {
        throw "Existing action drift for $($pushDefinition.Task); refusing update."
    }
    if ($pushTask.State -ne 'Ready' -or $pushTask.Settings.Enabled -ne $pushConfig.enabled -or
        $pushTask.Principal.LogonType -ne 'Interactive') {
        throw "Existing task state/identity drift for $($pushDefinition.Task); refusing update."
    }
    $pushFirst = [DateTimeOffset]::Parse($pushConfig.first_send_at).LocalDateTime
    $pushTriggers = @($pushConfig.hours | ForEach-Object {
        $pushAt = $pushFirst.Date.AddHours($_).AddMinutes($pushConfig.prepare_minute)
        if ($pushAt -lt $pushFirst) { $pushAt = $pushAt.AddDays(1) }
        New-ScheduledTaskTrigger -Daily -At $pushAt
    })
    $pushPlan += [pscustomobject]@{
        TaskName = $pushDefinition.Task
        OriginalTriggers = @($pushTask.Triggers)
        OriginalDescription = $pushTask.Description
        Triggers = $pushTriggers
        ExpectedHours = @($pushConfig.hours)
        ExpectedMinute = [int]$pushConfig.prepare_minute
        Description = "data-push paired local broadcast; starts :$('{0:D2}' -f $pushConfig.prepare_minute), retries every 2 minutes through :50. Live detail exists only while running; use view_live_push_status.ps1."
    }
}
$pushReadback = @()
$pushChanged = @()
try {
    foreach ($pushItem in $pushPlan) {
        $pushTask = Get-ScheduledTask -TaskName $pushItem.TaskName -ErrorAction Stop
        if ($pushTask.State -ne 'Ready') { throw "Task became active: $($pushItem.TaskName)" }
        $pushTask.Triggers = $pushItem.Triggers
        $pushTask.Description = $pushItem.Description
        Set-ScheduledTask -InputObject $pushTask | Out-Null
        $pushChanged += $pushItem
        $pushTask = Get-ScheduledTask -TaskName $pushItem.TaskName -ErrorAction Stop
        $pushInfo = $pushTask | Get-ScheduledTaskInfo
        $pushHours = @($pushTask.Triggers | ForEach-Object { ([DateTimeOffset]::Parse($_.StartBoundary)).Hour })
        $pushMinutes = @($pushTask.Triggers | ForEach-Object { ([DateTimeOffset]::Parse($_.StartBoundary)).Minute })
        if ((@($pushHours) -join ',') -ne (@($pushItem.ExpectedHours) -join ',') -or
            @($pushMinutes | Where-Object { $_ -ne $pushItem.ExpectedMinute }).Count -ne 0 -or
            $pushTask.Description -ne $pushItem.Description -or -not $pushTask.Settings.Enabled) {
            throw "Task trigger readback mismatch: $($pushItem.TaskName)"
        }
        $pushReadback += [pscustomobject]@{
            TaskName = $pushTask.TaskName
            State = $pushTask.State.ToString()
            Enabled = $pushTask.Settings.Enabled
            NextRunTime = $pushInfo.NextRunTime
            TriggerMinutes = $pushMinutes
            Action = $pushTask.Actions.Arguments
            Description = $pushTask.Description
        }
    }
} catch {
    $pushFailure = $_
    $pushRollbackErrors = @()
    foreach ($pushItem in $pushChanged) {
        try {
            $pushTask = Get-ScheduledTask -TaskName $pushItem.TaskName -ErrorAction Stop
            $pushTask.Triggers = $pushItem.OriginalTriggers
            $pushTask.Description = $pushItem.OriginalDescription
            Set-ScheduledTask -InputObject $pushTask | Out-Null
        } catch {
            $pushRollbackErrors += "$($pushItem.TaskName): $($_.Exception.Message)"
        }
    }
    throw "Task update failed: $pushFailure; rollback errors: $($pushRollbackErrors -join '; ')"
}
$pushReadback | ConvertTo-Json -Depth 5
