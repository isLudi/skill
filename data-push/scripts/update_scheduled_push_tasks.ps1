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
    @{ Config = 'supervisor_private_app_sync_scheduled_push.json'; Task = 'Codex-Lark-Supervisor-Private-App-Push'; Launcher = 'run_supervisor_private_app_sync_scheduled_push.ps1' }
)
$pushReadback = @()
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
    $pushFirst = [DateTimeOffset]::Parse($pushConfig.first_send_at).LocalDateTime
    $pushTriggers = @($pushConfig.hours | ForEach-Object {
        $pushAt = $pushFirst.Date.AddHours($_).AddMinutes($pushConfig.prepare_minute)
        if ($pushAt -lt $pushFirst) { $pushAt = $pushAt.AddDays(1) }
        New-ScheduledTaskTrigger -Daily -At $pushAt
    })
    $pushDescription = "data-push staggered local broadcast; starts :$('{0:D2}' -f $pushConfig.prepare_minute), retries every 2 minutes through :50. Live detail exists only while running; use view_live_push_status.ps1."
    $pushTask.Triggers = $pushTriggers
    $pushTask.Description = $pushDescription
    Set-ScheduledTask -InputObject $pushTask | Out-Null
    $pushTask = Get-ScheduledTask -TaskName $pushDefinition.Task
    $pushInfo = $pushTask | Get-ScheduledTaskInfo
    $pushReadback += [pscustomobject]@{
        TaskName = $pushTask.TaskName
        State = $pushTask.State.ToString()
        Enabled = $pushTask.Settings.Enabled
        NextRunTime = $pushInfo.NextRunTime
        TriggerMinutes = @($pushTask.Triggers | ForEach-Object { ([DateTimeOffset]::Parse($_.StartBoundary)).Minute })
        Action = $pushTask.Actions.Arguments
        Description = $pushTask.Description
    }
}
$pushReadback | ConvertTo-Json -Depth 5
