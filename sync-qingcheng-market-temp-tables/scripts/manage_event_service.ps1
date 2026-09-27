[CmdletBinding()]
param(
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'run-foreground', 'install-startup', 'uninstall-startup')]
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
        $process = Get-Process -Id ([int]$serviceStatus.pid) -ErrorAction SilentlyContinue
        return $null -ne $process
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
    $statusPath = Join-Path $runtimeRoot 'status.json'
    if (Test-ServiceProcess -StatusPath $statusPath) {
        Show-Status
        return
    }
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
    $deadline = (Get-Date).AddSeconds(30)
    do {
        Start-Sleep -Milliseconds 500
        if (Test-Path -LiteralPath $statusPath) {
            $serviceStatus = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($serviceStatus.status -in @('running', 'failed')) {
                break
            }
        }
    } while ((Get-Date) -lt $deadline)
    Show-Status
}

function Stop-ServiceProcess {
    $runtimeRoot = Get-RuntimeRoot
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
    & $Python $ServiceScript validate-config --config $ConfigPath
    if ($LASTEXITCODE -ne 0) {
        throw 'Configuration validation failed.'
    }
    & $Python $ServiceScript run --config $ConfigPath
    exit $LASTEXITCODE
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
            -Trigger $taskTrigger `
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
    'uninstall-startup' {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($null -ne $task) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }
        [PSCustomObject]@{ TaskName = $TaskName; Installed = $false }
    }
}
