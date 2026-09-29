param([switch]$Watch, [ValidateRange(1, 60)][int]$RefreshSeconds = 5)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

# Reads the durable per-run verdicts the broadcaster appends under the
# machine-local `paths.push_log_root`. The previous version read live-status.json
# inside each state directory, which never existed: `live_status` deletes that
# file at the end of every run, so the table was always empty.
# Keep this file ASCII-only: PowerShell 5.1 reads .ps1 as ANSI, and the
# repository convention is UTF-8 without BOM, so non-ASCII source breaks parsing.
$codexHome = (Resolve-Path -LiteralPath (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') '..') '..')).Path
$machine = Get-Content -LiteralPath (Join-Path $codexHome 'machine.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$logRoot = $machine.paths.push_log_root
if (-not $logRoot) { throw 'machine.local.json paths.push_log_root is not configured' }
$index = Join-Path (Join-Path $logRoot '_index') 'runs.jsonl'

do {
    if ($Watch) { Clear-Host }
    if (-not (Test-Path -LiteralPath $index -PathType Leaf)) {
        Write-Output "no run log yet: $index"
        Write-Output 'It appears after the push scripts have run once.'
    } else {
        $runs = Get-Content -LiteralPath $index -Encoding UTF8 | ForEach-Object {
            try { $_ | ConvertFrom-Json } catch { $null }
        } | Where-Object { $_ }
        $rows = $runs | Group-Object task_name | ForEach-Object {
            $last = $_.Group[-1]
            $task = Get-ScheduledTask -TaskName $last.task_name -ErrorAction SilentlyContinue
            $info = if ($task) { $task | Get-ScheduledTaskInfo } else { $null }
            [pscustomobject]@{
                Channel = $last.channel_id
                Slot = $last.slot
                Exit = $last.exit_code
                LastEvent = $last.last_event
                NeedsAttention = ($last.needs_attention -join ', ')
                NextRun = if ($info) { $info.NextRunTime } else { $null }
            }
        }
        $rows | Sort-Object Channel | Format-Table -AutoSize -Wrap
        $attention = $rows | Where-Object { $_.Exit -ne 0 -or $_.NeedsAttention }
        if ($attention) {
            Write-Output ''
            Write-Output 'needs attention:'
            $attention | ForEach-Object {
                Write-Output ("  {0}  slot={1}  last_event={2}" -f $_.Channel, $_.Slot, $_.LastEvent)
                if ($_.NeedsAttention) { Write-Output ("      blocked channels: " + $_.NeedsAttention) }
            }
        }
    }
    if ($Watch) { Start-Sleep -Seconds $RefreshSeconds }
} while ($Watch)
