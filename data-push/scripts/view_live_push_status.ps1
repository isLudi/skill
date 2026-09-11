param([switch]$Watch, [ValidateRange(1, 60)][int]$RefreshSeconds = 2)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$pushDefinitions = @(
    @{ Task = 'Codex-Lark-Market-KOC-GroupPush'; Status = 'C:\Users\Ludim\.codex\runtime\channel-broadcast-push\scheduled\live-status.json' },
    @{ Task = 'Codex-Lark-Business-KOC-Math-Push'; Status = 'C:\Users\Ludim\.codex\runtime\channel-broadcast-push\business-koc-math\live-status.json' },
    @{ Task = 'Codex-Lark-Supervisor-KOC-Douyin-Push'; Status = 'C:\Users\Ludim\.codex\runtime\channel-broadcast-push\supervisor-koc-douyin-sync\live-status.json' },
    @{ Task = 'Codex-Lark-Supervisor-Private-App-Push'; Status = 'C:\Users\Ludim\.codex\runtime\channel-broadcast-push\supervisor-private-app-sync\live-status.json' }
)
do {
    if ($Watch) { Clear-Host }
    $pushRows = foreach ($pushDefinition in $pushDefinitions) {
        $pushTask = Get-ScheduledTask -TaskName $pushDefinition.Task -ErrorAction SilentlyContinue
        $pushInfo = if ($pushTask) { $pushTask | Get-ScheduledTaskInfo } else { $null }
        $pushLive = if (Test-Path -LiteralPath $pushDefinition.Status) {
            Get-Content -LiteralPath $pushDefinition.Status -Encoding UTF8 -Raw | ConvertFrom-Json
        } else { $null }
        [pscustomobject]@{
            TaskName = $pushDefinition.Task
            TaskState = if ($pushTask) { $pushTask.State.ToString() } else { 'Missing' }
            LastTaskResult = if ($pushInfo) { '0x{0:X8}' -f ([uint32]$pushInfo.LastTaskResult) } else { $null }
            NextRunTime = if ($pushInfo) { $pushInfo.NextRunTime } else { $null }
            CurrentStep = if ($pushLive) { $pushLive.event } else { $null }
            UpdatedAt = if ($pushLive) { $pushLive.at } else { $null }
            Attempt = if ($pushLive) { $pushLive.attempt } else { $null }
            Channel = if ($pushLive) { $pushLive.channel } else { $null }
            Reason = if ($pushLive) { $pushLive.reason } else { $null }
            NextRetryAt = if ($pushLive) { $pushLive.next_retry_at } else { $null }
        }
    }
    $pushRows | Format-Table -AutoSize -Wrap
    if ($Watch) { Start-Sleep -Seconds $RefreshSeconds }
} while ($Watch)
