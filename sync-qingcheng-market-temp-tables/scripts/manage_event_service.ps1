[CmdletBinding()]
param(
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'run-foreground', 'install-startup', 'ensure-autorestart', 'uninstall-startup')]
    [string]$Action = 'status',
    [string]$Config = 'C:\Users\lvshuai01\.codex\runtime\sync-qingcheng-market-temp-tables\event-service\config.json',
    [string]$TaskName = 'Codex-Governed-TempTables-LarkEvent'
)

$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$env:USQL_ENV_FILE = 'D:\GAOTU\19002_市场顾问部看板维护表格\usql_api.env'

$Python = 'D:\anaconda3\python.exe'
$SkillRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$ServiceScript = Join-Path $SkillRoot 'scripts\governed_temp_table_event_service.py'
$ConfigPath = [System.IO.Path]::GetFullPath($Config)

function Get-RuntimeRoot {
    if (-not (Test-Path -LiteralPath $ConfigPath)) {
        throw "Config does not exist: $ConfigPath"
    }
    $configObject = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $runtimeValue = [string]$configObject.runtime_root
    if ([string]::IsNullOrWhiteSpace($runtimeValue)) {
        throw 'Config field runtime_root is required.'
    }
    if ([System.IO.Path]::IsPathRooted($runtimeValue)) {
        return [System.IO.Path]::GetFullPath($runtimeValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $ConfigPath) $runtimeValue))
}

function Test-ServiceProcess {
    param([string]$StatusPath)
    if (-not (Test-Path -LiteralPath $StatusPath)) {
        return $false
    }
    try {
        $serviceStatus = Get-Content -LiteralPath $StatusPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $serviceStatus.pid) {
            return $false
        }
        $servicePid = [int]$serviceStatus.pid
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$servicePid" -ErrorAction SilentlyContinue
        return $null -ne $process -and $process.Name -match '^pythonw?\.exe$' -and
            $process.CommandLine -and $process.CommandLine.IndexOf($ServiceScript, [StringComparison]::OrdinalIgnoreCase) -ge 0
    }
    catch {
        return $false
    }
}

function Assert-InteractiveSession {
    $sessionId = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
    if ($sessionId -eq 0) {
        throw 'The event service must run in an interactive user session because Excel COM cannot open staged workbooks from Session 0.'
    }
}

function Show-Status {
    & $Python $ServiceScript status --config $ConfigPath
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to read service status.'
    }
}

function Start-ServiceProcess {
    Assert-InteractiveSession
    & $Python $ServiceScript validate-config --config $ConfigPath
    if ($LASTEXITCODE -ne 0) {
        throw 'Configuration validation failed.'
    }
    $runtimeRoot = Get-RuntimeRoot
    [System.IO.Directory]::CreateDirectory($runtimeRoot) | Out-Null
    $pausePath = Join-Path $runtimeRoot 'autorestart.paused'
    if (Test-Path -LiteralPath $pausePath) {
        Remove-Item -LiteralPath $pausePath -Force
    }
    $statusPath = Join-Path $runtimeRoot 'status.json'
    if (Test-ServiceProcess -StatusPath $statusPath) {
        Show-Status
        return
    }
    $scheduledTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    $matchingActions = if ($scheduledTask) {
        @($scheduledTask.Actions | Where-Object {
            $_.Arguments -and
            $_.Arguments.IndexOf($PSCommandPath, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
            $_.Arguments.IndexOf($ConfigPath, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
            $_.Arguments -match 'run-foreground'
        })
    } else { @() }
    if ($matchingActions.Count -eq 1) {
        if ($scheduledTask.State -eq 'Disabled') { throw 'The configured listener task is disabled.' }
        $taskDeadline = (Get-Date).AddSeconds(10)
        while ($scheduledTask.State -eq 'Running' -and (Get-Date) -lt $taskDeadline) {
            Start-Sleep -Milliseconds 250
            $scheduledTask = Get-ScheduledTask -TaskName $TaskName
        }
        if ($scheduledTask.State -eq 'Running') {
            throw 'The scheduled task is running without a verified listener process.'
        }
        Start-ScheduledTask -TaskName $TaskName
    } else {
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $stdoutPath = Join-Path $runtimeRoot "launcher-$stamp.stdout.log"
        $stderrPath = Join-Path $runtimeRoot "launcher-$stamp.stderr.log"
        Start-Process `
            -FilePath $Python `
            -ArgumentList @($ServiceScript, 'run', '--config', $ConfigPath) `
            -WorkingDirectory $SkillRoot `
            -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -PassThru | Out-Null
    }
    $deadline = (Get-Date).AddSeconds(30)
    do {
        Start-Sleep -Milliseconds 500
        if (Test-Path -LiteralPath $statusPath) {
            $serviceStatus = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($serviceStatus.status -eq 'failed' -or
                ($serviceStatus.status -eq 'running' -and (Test-ServiceProcess -StatusPath $statusPath))) {
                break
            }
        }
    } while ((Get-Date) -lt $deadline)
    Show-Status
    if (-not (Test-ServiceProcess -StatusPath $statusPath)) {
        throw 'The event service did not start a verified process.'
    }
}

function Stop-ServiceProcess {
    $runtimeRoot = Get-RuntimeRoot
    [System.IO.Directory]::CreateDirectory($runtimeRoot) | Out-Null
    [System.IO.File]::WriteAllText(
        (Join-Path $runtimeRoot 'autorestart.paused'),
        [DateTimeOffset]::Now.ToString('O'),
        [System.Text.UTF8Encoding]::new($false)
    )
    $statusPath = Join-Path $runtimeRoot 'status.json'
    if (-not (Test-ServiceProcess -StatusPath $statusPath)) {
        Show-Status
        return
    }
    [System.IO.File]::WriteAllText(
        (Join-Path $runtimeRoot 'stop.request'),
        [DateTimeOffset]::Now.ToString('O'),
        [System.Text.UTF8Encoding]::new($false)
    )
    $deadline = (Get-Date).AddSeconds(30)
    do {
        Start-Sleep -Milliseconds 500
        if (-not (Test-ServiceProcess -StatusPath $statusPath)) {
            break
        }
    } while ((Get-Date) -lt $deadline)
    Show-Status
    if (Test-ServiceProcess -StatusPath $statusPath) {
        throw 'Service is still finishing an in-flight job. It was not force-killed.'
    }
}

function Run-ForegroundService {
    Assert-InteractiveSession
    $runtimeRoot = Get-RuntimeRoot
    if (Test-Path -LiteralPath (Join-Path $runtimeRoot 'autorestart.paused')) {
        Write-Output 'Automatic event-service recovery is paused by an explicit stop.'
        exit 0
    }
    & $Python $ServiceScript validate-config --config $ConfigPath
    if ($LASTEXITCODE -ne 0) {
        throw 'Configuration validation failed.'
    }
    & $Python $ServiceScript run --config $ConfigPath
    exit $LASTEXITCODE
}

function New-EventRecoveryTrigger {
    $trigger = New-ScheduledTaskTrigger -Daily -At ([DateTime]::Today)
    $trigger.Id = 'CodexEventRecovery'
    $trigger.Repetition = New-CimInstance `
        -ClassName MSFT_TaskRepetitionPattern `
        -Namespace 'Root/Microsoft/Windows/TaskScheduler' `
        -Property @{ Interval = 'PT2M'; Duration = 'P1D'; StopAtDurationEnd = $false } `
        -ClientOnly
    return $trigger
}

function Ensure-AutoRestartTrigger {
    Assert-InteractiveSession
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    if ($task.State -eq 'Disabled' -or $task.Principal.LogonType -ne 'Interactive' -or $task.Settings.MultipleInstances -ne 'IgnoreNew') {
        throw 'Recovery requires an enabled interactive task with IgnoreNew concurrency.'
    }
    $recoveryTriggers = @($task.Triggers | Where-Object { $_.Id -eq 'CodexEventRecovery' })
    if ($recoveryTriggers.Count -gt 1) {
        throw 'Multiple event recovery triggers exist; inspect the task before changing it.'
    }
    if ($recoveryTriggers.Count -eq 1) {
        $existing = $recoveryTriggers[0]
        if ($existing.Enabled -and $existing.Repetition.Interval -eq 'PT2M' -and $existing.Repetition.Duration -eq 'P1D' -and -not $existing.Repetition.StopAtDurationEnd) {
            return [PSCustomObject]@{ TaskName = $TaskName; Status = 'already_configured'; Interval = 'PT2M' }
        }
        throw 'Existing event recovery trigger differs from the expected schedule.'
    }
    $runtimeRoot = Get-RuntimeRoot
    $backupPath = Join-Path $runtimeRoot ('task-before-autorestart-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.xml')
    if (Test-Path -LiteralPath $backupPath) { throw 'Task backup already exists.' }
    $beforeText = Export-ScheduledTask -TaskName $TaskName
    $backupText = $beforeText -replace 'encoding="UTF-16"', 'encoding="UTF-8"'
    [System.IO.File]::WriteAllText($backupPath, $backupText, [System.Text.UTF8Encoding]::new($false))
    [xml](Get-Content -LiteralPath $backupPath -Raw -Encoding UTF8) | Out-Null
    [xml]$before = $beforeText
    $triggers = @($task.Triggers) + @(New-EventRecoveryTrigger)
    Set-ScheduledTask -TaskName $TaskName -Trigger $triggers | Out-Null
    [xml]$after = Export-ScheduledTask -TaskName $TaskName
    if ($before.Task.Principals.OuterXml -ne $after.Task.Principals.OuterXml -or
        $before.Task.Actions.OuterXml -ne $after.Task.Actions.OuterXml -or
        $before.Task.Settings.OuterXml -ne $after.Task.Settings.OuterXml) {
        throw "Task identity, actions or settings changed unexpectedly; inspect $backupPath."
    }
    $updated = Get-ScheduledTask -TaskName $TaskName
    $verified = @($updated.Triggers | Where-Object { $_.Id -eq 'CodexEventRecovery' })
    if ($verified.Count -ne 1 -or -not $verified[0].Enabled -or
        $verified[0].Repetition.Interval -ne 'PT2M' -or $verified[0].Repetition.Duration -ne 'P1D' -or
        $verified[0].Repetition.StopAtDurationEnd) {
        throw "Event recovery trigger readback failed; inspect $backupPath."
    }
    return [PSCustomObject]@{ TaskName = $TaskName; Status = 'configured'; Interval = 'PT2M'; Backup = $backupPath }
}

switch ($Action) {
    'start' {
        Start-ServiceProcess
    }
    'stop' {
        Stop-ServiceProcess
    }
    'restart' {
        Stop-ServiceProcess
        Start-ServiceProcess
    }
    'status' {
        Show-Status
    }
    'logs' {
        $logPath = Join-Path (Get-RuntimeRoot) 'service.log'
        if (Test-Path -LiteralPath $logPath) {
            Get-Content -LiteralPath $logPath -Tail 200 -Encoding UTF8
        }
        else {
            throw "Log does not exist: $logPath"
        }
    }
    'run-foreground' {
        Run-ForegroundService
    }
    'install-startup' {
        & $Python $ServiceScript validate-config --config $ConfigPath
        if ($LASTEXITCODE -ne 0) {
            throw 'Configuration validation failed.'
        }
        $powerShell = (Get-Command powershell.exe).Source
        $arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`" -Action run-foreground -Config `"$ConfigPath`""
        $taskAction = New-ScheduledTaskAction -Execute $powerShell -Argument $arguments
        $taskTrigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
        $taskRecoveryTrigger = New-EventRecoveryTrigger
        $taskPrincipal = New-ScheduledTaskPrincipal `
            -UserId "$env:USERDOMAIN\$env:USERNAME" `
            -LogonType Interactive `
            -RunLevel Limited
        $taskSettings = New-ScheduledTaskSettingsSet `
            -Hidden `
            -MultipleInstances IgnoreNew `
            -RestartCount 3 `
            -RestartInterval (New-TimeSpan -Minutes 2) `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -DontStopOnIdleEnd `
            -StartWhenAvailable
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $taskAction `
            -Trigger @($taskTrigger, $taskRecoveryTrigger) `
            -Principal $taskPrincipal `
            -Settings $taskSettings `
            -Description 'Start the governed Qingcheng and market-consultant temp-table event service at user logon.' `
            -Force | Out-Null
        $task = Get-ScheduledTask -TaskName $TaskName
        if ($task.Principal.LogonType -ne 'Interactive') {
            throw 'The event service startup task did not retain its interactive logon type.'
        }
        $task | Select-Object TaskName, State
    }
    'ensure-autorestart' {
        Ensure-AutoRestartTrigger
    }
    'uninstall-startup' {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($null -ne $task) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }
        [PSCustomObject]@{ TaskName = $TaskName; Installed = $false }
    }
}
