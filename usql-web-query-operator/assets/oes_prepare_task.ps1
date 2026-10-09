param(
    [string]$TaskName = 'OES-Base-Sync',
    [string]$BundleRoot = $PSScriptRoot,
    [string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
if ($TaskName -match '[\\/"\x00-\x1f]' -or [string]::IsNullOrWhiteSpace($TaskName)) {
    throw 'TaskName must be a single nonempty task name without path separators or quotes.'
}
$oesBundle = (Resolve-Path -LiteralPath $BundleRoot).Path
$oesPythonw = Join-Path $oesBundle '.venv/Scripts/pythonw.exe'
$oesLauncher = Join-Path $oesBundle 'skills/usql-web-query-operator/scripts/run_oes_base_silent.py'
$oesSettings = Join-Path $oesBundle 'settings.json'
$oesTemplate = Join-Path $oesBundle 'task-scheduler/task-template.xml'
foreach ($oesFile in @($oesPythonw, $oesLauncher, $oesSettings, $oesTemplate)) {
    if (-not (Test-Path -LiteralPath $oesFile -PathType Leaf)) {
        throw "Required deployment file missing: $oesFile. Run setup.ps1 and configure settings first."
    }
}
if (-not $OutputPath) { $OutputPath = Join-Path $oesBundle 'task-scheduler/oes-base.task.xml' }
$oesOutput = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $oesOutput) {
    throw 'Output XML already exists; use another OutputPath to preserve the reviewed file.'
}
$oesOutputParent = [IO.Path]::GetDirectoryName($oesOutput)
if (-not (Test-Path -LiteralPath $oesOutputParent -PathType Container)) {
    throw 'Output parent directory must already exist.'
}
[xml]$oesXml = [IO.File]::ReadAllText($oesTemplate, [Text.Encoding]::UTF8)
$oesNs = [Xml.XmlNamespaceManager]::new($oesXml.NameTable)
$oesNs.AddNamespace('t', 'http://schemas.microsoft.com/windows/2004/02/mit/task')
function Set-OesNode([string]$XPath, [string]$Value) {
    $oesNode = $oesXml.SelectSingleNode($XPath, $oesNs)
    if (-not $oesNode) { throw "Task template node missing: $XPath" }
    $oesNode.InnerText = $Value
}
$oesAccountSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$oesShanghai = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'China Standard Time')
$oesStart = $oesShanghai.Date.AddMinutes(([Math]::Floor($oesShanghai.TimeOfDay.TotalMinutes / 30) + 1) * 30)
Set-OesNode '/t:Task/t:RegistrationInfo/t:URI' ('\' + $TaskName)
Set-OesNode '/t:Task/t:Principals/t:Principal/t:UserId' $oesAccountSid
Set-OesNode '/t:Task/t:Triggers/t:CalendarTrigger/t:StartBoundary' ($oesStart.ToString('yyyy-MM-ddTHH:mm:ss') + '+08:00')
Set-OesNode '/t:Task/t:Actions/t:Exec/t:Command' $oesPythonw
Set-OesNode '/t:Task/t:Actions/t:Exec/t:Arguments' ('"' + $oesLauncher + '" --settings "' + $oesSettings + '"')
Set-OesNode '/t:Task/t:Actions/t:Exec/t:WorkingDirectory' $oesBundle
$oesWriterSettings = [Xml.XmlWriterSettings]::new()
$oesWriterSettings.Encoding = [Text.Encoding]::Unicode
$oesWriterSettings.Indent = $true
$oesWriter = [Xml.XmlWriter]::Create($oesOutput, $oesWriterSettings)
try { $oesXml.Save($oesWriter) } finally { $oesWriter.Dispose() }
[ordered]@{ status='generated_disabled'; xml=$oesOutput; task_name=$TaskName; user_sid=$oesAccountSid;
    interval_minutes=30; logon_type='InteractiveToken'; hidden=$true; registered=$false;
    power_settings_changed=$false } | ConvertTo-Json
