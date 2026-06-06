param([switch]$Push)

$source = "C:\Users\Ludim\.codex\AGENTS.md"
$dest   = "C:\Users\Ludim\.codex\skills\AGENTS.md"

if (-not (Test-Path $source)) {
    Write-Error "Source not found: $source"
    exit 1
}

Copy-Item -Path $source -Destination $dest -Force
Write-Host "Synced: $source -> $dest"

Set-Location "C:\Users\Ludim\.codex\skills"
git add AGENTS.md

$diff = git diff --cached --quiet AGENTS.md 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "AGENTS.md unchanged, nothing to commit."
} else {
    git commit -m "Sync AGENTS.md from .codex root"
    Write-Host "Committed AGENTS.md sync."
}

if ($Push) {
    git push origin main
    Write-Host "Pushed to origin/main."
}
