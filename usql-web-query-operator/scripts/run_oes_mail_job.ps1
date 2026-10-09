[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$JobConfig,
    [Parameter(Mandatory = $true)][string]$OutputDir,
    [Parameter(Mandatory = $true)][string]$RunKey
)

$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

$taskCodexRoot = ([System.IO.DirectoryInfo]$PSScriptRoot).Parent.Parent.Parent.FullName
$taskMachineFile = Join-Path $taskCodexRoot 'machine.local.json'
$taskMachine = Get-Content -LiteralPath $taskMachineFile -Encoding UTF8 | ConvertFrom-Json
$taskPython = $taskMachine.executables.python
if (-not $taskPython -or -not (Test-Path -LiteralPath $taskPython -PathType Leaf)) {
    throw 'Configured machine.local.json executables.python is unavailable.'
}
if (-not (Test-Path -LiteralPath $JobConfig -PathType Leaf)) {
    throw 'JobConfig must be an existing JSON file.'
}
$taskArguments = @(
    (Join-Path $PSScriptRoot 'oes_achievement.py'), 'export-and-download',
    '--config-file', (Resolve-Path -LiteralPath $JobConfig).Path,
    '--output-dir', $OutputDir, '--run-key', $RunKey
)
& $taskPython @taskArguments
exit $LASTEXITCODE
