[CmdletBinding()]
param(
    [ValidateSet("Export", "Import", "Check")]
    [string]$Mode = "Export",
    [switch]$ConfirmImport,
    [switch]$Commit,
    [switch]$NoCommit,
    [switch]$Push
)

$ErrorActionPreference = "Stop"

if ($Commit -and $NoCommit) {
    throw "-Commit cannot be combined with -NoCommit."
}
if ($Mode -eq "Check" -and ($Commit -or $Push -or $ConfirmImport)) {
    throw "Check mode is read-only; -Commit, -Push and -ConfirmImport are not valid."
}
if ($ConfirmImport -and $Mode -ne "Import") {
    throw "-ConfirmImport is valid only with Import mode."
}
if ($Push -and -not $Commit) {
    throw "-Push requires explicit -Commit authorization."
}

$repoRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$codexRoot = Split-Path -Parent $repoRoot
$canonicalAgents = Join-Path $repoRoot "AGENTS.md"
$runtimeAgents = Join-Path $codexRoot "WORKSPACE_AGENTS.md"
$layoutChecker = Join-Path $repoRoot "scripts\check_agents_layout.py"
$pythonExe = "D:\anaconda3\python.exe"
$trackedPath = "AGENTS.md"

function Get-FileSha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }
    $stream = [System.IO.File]::OpenRead($Path)
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        return [System.BitConverter]::ToString($hasher.ComputeHash($stream)).Replace("-", "")
    } finally {
        $hasher.Dispose()
        $stream.Dispose()
    }
}

function Invoke-LayoutCheck {
    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        throw "Required Python interpreter not found: $pythonExe"
    }
    if (-not (Test-Path -LiteralPath $layoutChecker -PathType Leaf)) {
        throw "AGENTS layout checker not found: $layoutChecker"
    }
    & $pythonExe $layoutChecker
    if ($LASTEXITCODE -ne 0) {
        throw "AGENTS layout validation failed."
    }
}

if ($Mode -eq "Check") {
    Invoke-LayoutCheck
    exit 0
}

if ($Mode -eq "Import" -and -not $ConfirmImport) {
    throw "Import replaces the Git-versioned AGENTS.md. Re-run with -ConfirmImport after reviewing the runtime mirror."
}

if ($Mode -eq "Export") {
    $source = $canonicalAgents
    $destination = $runtimeAgents
} else {
    $source = $runtimeAgents
    $destination = $canonicalAgents
}

if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Source not found: $source"
}

Copy-Item -LiteralPath $source -Destination $destination -Force
if ((Get-FileSha256 $source) -ne (Get-FileSha256 $destination)) {
    throw "AGENTS synchronization hash verification failed."
}

Write-Host "Synced ($Mode): $source -> $destination"
Invoke-LayoutCheck

if ($Commit) {
    git -C $repoRoot add -- $trackedPath
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to stage $trackedPath."
    }

    git -C $repoRoot diff --cached --quiet -- $trackedPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "AGENTS.md unchanged, nothing to commit."
    } elseif ($LASTEXITCODE -eq 1) {
        git -C $repoRoot commit --only -m "Update Codex workspace instructions" -- $trackedPath
        if ($LASTEXITCODE -ne 0) {
            throw "Git commit failed."
        }
        Write-Host "Committed AGENTS.md."
    } else {
        throw "Unable to inspect the staged AGENTS.md diff."
    }
}

if ($Push) {
    $currentBranch = git -C $repoRoot branch --show-current
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($currentBranch)) {
        throw "Unable to resolve the current Git branch."
    }
    git -C $repoRoot push origin $currentBranch
    if ($LASTEXITCODE -ne 0) {
        throw "Git push failed."
    }
    Write-Host "Pushed to origin/$currentBranch."
}
