[CmdletBinding()]
param(
    # Check: report drift only. Merge: copy mtime-newer files into the repo.
    # Link: replace workbuddy-side shared dirs with junctions into the repo.
    [ValidateSet("Check", "Merge", "Link")]
    [string]$Mode = "Check",
    # Where to move workbuddy-side originals during Link. Default: timestamped backup dir.
    [string]$BackupRoot = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Resolve-Path -LiteralPath $PSScriptRoot).Path
$workbuddyRoot = "C:\Users\lvshuai01\.workbuddy\skills"
$manifestPath = Join-Path $repoRoot "shared-skills.json"

# WorkBuddy platform-managed skills: never synced, never committed here.
$platformOnly = @("imagegen", "openai-docs", "plugin-creator", "review-agent", "skill-creator", "skill-installer")
# Repo-internal top-level entries that must not be treated as shared skills.
$repoOnlyTop = @(".git", ".system", ".pytest_cache")
# Directory names skipped during file scans.
$skipDirNames = @("__pycache__", ".pytest_cache", "node_modules", ".git", ".venv", "venv")

function Get-FileSha256([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        return [System.BitConverter]::ToString($hasher.ComputeHash($stream)).Replace("-", "")
    } finally {
        $hasher.Dispose()
        $stream.Dispose()
    }
}

function Get-SkillFiles([string]$Root) {
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return @() }
    Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Where-Object {
        $rel = $_.FullName.Substring($Root.Length).TrimStart('\')
        $parts = $rel -split '\\'
        -not ($parts | Where-Object { $skipDirNames -contains $_ })
    }
}

function Get-SharedSkills {
    $repoDirs = Get-ChildItem -LiteralPath $repoRoot -Directory -Force | Where-Object {
        ($repoOnlyTop -notcontains $_.Name) -and (-not $_.Name.StartsWith("."))
    } | Select-Object -ExpandProperty Name
    $wbDirs = Get-ChildItem -LiteralPath $workbuddyRoot -Directory -Force | Where-Object {
        ($platformOnly -notcontains $_.Name) -and (-not $_.Name.StartsWith("."))
    } | Select-Object -ExpandProperty Name
    $shared = @($repoDirs | Where-Object { $wbDirs -contains $_ } | Sort-Object)
    $repoOnly = @($repoDirs | Where-Object { $wbDirs -notcontains $_ } | Sort-Object)
    $wbOnly = @($wbDirs | Where-Object { $repoDirs -notcontains $_ } | Sort-Object)
    return [PSCustomObject]@{ Shared = $shared; RepoOnly = $repoOnly; WorkbuddyOnly = $wbOnly }
}

function Write-Manifest([string[]]$Shared) {
    $manifest = [ordered]@{
        description = "Shared skill set between ~/.workbuddy/skills (junction consumers) and this git repo (canonical store)."
        canonical = $repoRoot
        consumer = $workbuddyRoot
        updated = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
        shared = @($shared)
        platform_managed_excluded = $platformOnly
        repo_internal_excluded = $repoOnlyTop
    }
    ($manifest | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    Write-Host "Manifest written: $manifestPath ($($Shared.Count) shared skills)"
}

$sets = Get-SharedSkills
Write-Host "Shared skills: $($sets.Shared.Count); repo-only: $($sets.RepoOnly.Count); workbuddy-only (unexpected): $($sets.WorkbuddyOnly.Count)"
if ($sets.WorkbuddyOnly.Count -gt 0) {
    Write-Host "WARNING: workbuddy dirs missing from repo (not synced): $($sets.WorkbuddyOnly -join ', ')"
}
if ($sets.RepoOnly.Count -gt 0) {
    Write-Host "Repo-only dirs (Link will expose them to workbuddy): $($sets.RepoOnly -join ', ')"
}

if ($Mode -eq "Check" -or $Mode -eq "Merge") {
    $copiedNew = 0; $copiedNewer = 0; $repoNewer = 0; $identical = 0
    foreach ($skill in $sets.Shared) {
        $wbDir = Join-Path $workbuddyRoot $skill
        $repoDir = Join-Path $repoRoot $skill
        foreach ($file in (Get-SkillFiles $wbDir)) {
            $rel = $file.FullName.Substring($wbDir.Length).TrimStart('\')
            $repoFile = Join-Path $repoDir $rel
            if (-not (Test-Path -LiteralPath $repoFile -PathType Leaf)) {
                if ($Mode -eq "Merge") {
                    $targetDir = Split-Path -Parent $repoFile
                    if (-not (Test-Path -LiteralPath $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
                    Copy-Item -LiteralPath $file.FullName -Destination $repoFile -Force
                }
                $copiedNew++
                Write-Host "  [new->repo] $skill\$rel"
                continue
            }
            if ((Get-FileSha256 $file.FullName) -eq (Get-FileSha256 $repoFile)) { $identical++; continue }
            $repoItem = Get-Item -LiteralPath $repoFile -Force
            if ($file.LastWriteTimeUtc -gt $repoItem.LastWriteTimeUtc) {
                if ($Mode -eq "Merge") {
                    Copy-Item -LiteralPath $file.FullName -Destination $repoFile -Force
                }
                $copiedNewer++
                Write-Host "  [wb newer->repo] $skill\$rel"
            } else {
                $repoNewer++
                Write-Host "  [repo newer, kept] $skill\$rel"
            }
        }
    }
    Write-Host "Scan complete: identical=$identical, workbuddy-newer=$copiedNewer, workbuddy-only-files=$copiedNew, repo-newer-kept=$repoNewer"
    if ($Mode -eq "Merge") {
        Write-Manifest $sets.Shared
        Write-Host "Merge done. Review with: git -C `"$repoRoot`" status --short"
    } else {
        Write-Host "Check mode: no files were modified."
    }
    exit 0
}

# Link mode
if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $BackupRoot = "C:\Users\lvshuai01\.workbuddy\skills-backup-" + (Get-Date -Format "yyyy-MM-dd-HHmm")
}
$linkTargets = @($sets.Shared) + @($sets.RepoOnly)
$linked = 0; $skipped = 0
foreach ($skill in $linkTargets) {
    $wbPath = Join-Path $workbuddyRoot $skill
    $repoPath = Join-Path $repoRoot $skill
    if (-not (Test-Path -LiteralPath $repoPath -PathType Container)) {
        throw "Repo skill dir missing, cannot link: $repoPath"
    }
    $wbItem = Get-Item -LiteralPath $wbPath -Force -ErrorAction SilentlyContinue
    if ($wbItem -and ($wbItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        Write-Host "  [already linked] $skill"
        $skipped++
        continue
    }
    if ($wbItem) {
        if (-not (Test-Path -LiteralPath $BackupRoot)) { New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null }
        Move-Item -LiteralPath $wbPath -Destination (Join-Path $BackupRoot $skill)
        Write-Host "  [backed up] $skill -> $BackupRoot"
    }
    New-Item -ItemType Junction -Path $wbPath -Target $repoPath | Out-Null
    $newItem = Get-Item -LiteralPath $wbPath -Force
    $actualTarget = $newItem.Target
    if ($actualTarget -is [array]) { $actualTarget = $actualTarget[0] }
    if ($newItem.LinkType -ne "Junction" -or $actualTarget -ne $repoPath) {
        throw "Junction verification failed for ${skill}: LinkType=$($newItem.LinkType), Target=$actualTarget"
    }
    $linked++
    Write-Host "  [linked] $skill -> $repoPath"
}
Write-Manifest @($sets.Shared)
Write-Host "Link done: $linked linked, $skipped already linked. Backup: $BackupRoot"
