param([switch]$Preflight)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$usqlEnvCandidates = @(Get-ChildItem -LiteralPath 'D:\GAOTU' -Directory -Filter '19002_*' -ErrorAction Stop |
    ForEach-Object { Join-Path $_.FullName 'usql_api.env' } |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
if ($usqlEnvCandidates.Count -ne 1) { throw 'Expected exactly one 19002_*/usql_api.env under D:\GAOTU.' }
$env:USQL_ENV_FILE = $usqlEnvCandidates[0]
$pushPython = 'D:\anaconda3\python.exe'
$pushScheduler = Join-Path $PSScriptRoot 'scheduled_push.py'
$pushConfig = Join-Path (Split-Path $PSScriptRoot -Parent) 'config\supervisor_yafei_grade_9_advisor_scheduled_push.json'
$pushArguments = @('-u', $pushScheduler, '--config', $pushConfig)
if ($Preflight) { $pushArguments += '--preflight' }
else { $pushArguments += @('--watch', '--confirm-send') }
# External run log. Covers crashes and argparse errors that never reach emit();
# a logging failure must never block a push, so this degrades instead of throwing.
$pushLog = $null
try {
    $codexHome = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
    $machine = Get-Content -LiteralPath (Join-Path $codexHome 'machine.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $pushLogRoot = $machine.paths.push_log_root
    if (-not $pushLogRoot) { throw 'machine.local.json paths.push_log_root is not configured' }
    # Name the folder after the channel so the process log sits beside the
    # Python event stream instead of in a second, script-named tree.
    $pushChannel = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Name)
    try {
        $pushPointer = Get-Content -LiteralPath $pushConfig -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($pushPointer.channel_ref) { $pushChannel = ($pushPointer.channel_ref -split '/')[-1] }
    } catch { }
    $pushLogDir = Join-Path (Join-Path (Join-Path $pushLogRoot 'market_consultant') $pushChannel) (Get-Date -Format 'yyyy-MM-dd')
    New-Item -ItemType Directory -Force -Path $pushLogDir | Out-Null
    $pushLog = Join-Path $pushLogDir ((Get-Date -Format 'HHmmss') + '-process.log')
} catch {
    Write-Warning ('push run log unavailable: ' + $_.Exception.Message)
}
if ($pushLog) {
    # Explicit UTF-8 without BOM: Tee-Object would write UTF-16 on PowerShell 5.1.
    $pushLogEncoding = New-Object System.Text.UTF8Encoding($false)
    & $pushPython @pushArguments 2>&1 | ForEach-Object { [System.IO.File]::AppendAllText($pushLog, [string]$_ + [Environment]::NewLine, $pushLogEncoding) }
} else {
    & $pushPython @pushArguments 2>&1 | Out-Null
}
exit $LASTEXITCODE
