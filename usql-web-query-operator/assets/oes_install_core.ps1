# Windows PowerShell 5.1 compatible; UI strings are loaded separately as UTF-8.
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:LARKSUITE_CLI_NO_UPDATE_NOTIFIER = '1'
$env:LARKSUITE_CLI_NO_SKILLS_NOTIFIER = '1'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$script:OesUtf8 = [Text.UTF8Encoding]::new($false)
if (-not ('OesFiles.Native' -as [type])) {
    Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
namespace OesFiles {
    public static class Native {
        [DllImport("kernel32.dll", EntryPoint="MoveFileExW", CharSet=CharSet.Unicode, SetLastError=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool MoveFileEx(string source, string destination, uint flags);
    }
}
'@
}

function Get-OesSid { [Security.Principal.WindowsIdentity]::GetCurrent().User.Value }

function Get-OesHash([string]$Value) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { ([BitConverter]::ToString($sha.ComputeHash($script:OesUtf8.GetBytes($Value)))).Replace('-','').ToLower() }
    finally { $sha.Dispose() }
}

function Assert-OesLocalRoot([string]$Root) {
    $full = [IO.Path]::GetFullPath($Root).TrimEnd('\','/')
    if ($full.StartsWith('\\') -or $full.Length -lt 8 -or $full.Length -gt 150 -or
        $full -match '["\x00-\x1f]' -or $full -eq [IO.Path]::GetPathRoot($full).TrimEnd('\')) {
        throw 'Invalid installation directory.'
    }
    for ($parent = $full; $parent; $parent = [IO.Path]::GetDirectoryName($parent)) {
        if ((Test-Path -LiteralPath $parent) -and
            ((Get-Item -LiteralPath $parent -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Installation paths cannot contain junctions or symbolic links.'
        }
    }
    return $full
}

function Get-OesChildPath([string]$Root, [string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative) -or $Relative -match '(^|[/\\])\.\.([/\\]|$)|[:\x00]') {
        throw 'Unsafe bundle-relative path.'
    }
    $full = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $full.StartsWith($Root.TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar,
                              [StringComparison]::OrdinalIgnoreCase)) { throw 'Path escaped its root.' }
    for ($component=$full; $component -and $component.Length -ge $Root.Length;
         $component=[IO.Path]::GetDirectoryName($component)) {
        $item=Get-Item -LiteralPath $component -Force -ErrorAction SilentlyContinue
        if ($null -ne $item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Bundle paths cannot follow reparse points.'
        }
    }
    return $full
}

function Write-OesJson([string]$Path, $Value) {
    $temp = $Path + '.tmp'
    [IO.File]::WriteAllText($temp, ($Value | ConvertTo-Json -Depth 20), $script:OesUtf8)
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        if ([OesFiles.Native]::MoveFileEx($temp, $Path, 9)) { return }
        $code=[Runtime.InteropServices.Marshal]::GetLastWin32Error()
        if ($code -notin @(5,32,33)) { throw ('Atomic local JSON replacement failed: ' + $code) }
        Start-Sleep -Milliseconds 100
    }
    throw 'Atomic local JSON replacement remained locked; no job was started.'
}

function Read-OesJson([string]$Path) {
    [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8) | ConvertFrom-Json
}

function Set-OesPrivateAcl([string]$Path) {
    # Access-only descriptor avoids requiring SeSecurityPrivilege for SACL changes.
    $acl = [IO.Directory]::GetAccessControl($Path, [Security.AccessControl.AccessControlSections]::Access)
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($old in @($acl.Access)) { $acl.RemoveAccessRuleSpecific($old) }
    $inherit = [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit'
    foreach ($sid in @((Get-OesSid), 'S-1-5-18', 'S-1-5-32-544')) {
        $rule = [Security.AccessControl.FileSystemAccessRule]::new(
            [Security.Principal.SecurityIdentifier]::new($sid), 'FullControl', $inherit,
            [Security.AccessControl.PropagationFlags]::None, [Security.AccessControl.AccessControlType]::Allow)
        $acl.AddAccessRule($rule)
    }
    [IO.Directory]::SetAccessControl($Path, $acl)
}

function Test-OesManifest([string]$Root) {
    $manifest = Read-OesJson (Join-Path $Root 'bundle-manifest.json')
    if ($manifest.contains_credentials -ne $false -or @($manifest.files).Count -lt 10) {
        throw 'Invalid deployment manifest.'
    }
    $seen = @{}
    foreach ($entry in $manifest.files) {
        if ($seen.ContainsKey($entry.path)) { throw 'Duplicate manifest path.' }
        $seen[$entry.path] = $true
        $path = Get-OesChildPath $Root $entry.path
        # settings.json is intentionally mutable after installation.
        if ($entry.path -eq 'settings.json' -and (Test-Path -LiteralPath (Join-Path $Root 'private/install-state.json'))) { continue }
        if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or
            (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -ne $entry.sha256) {
            throw ('Bundle checksum mismatch: ' + $entry.path)
        }
    }
    return $manifest
}

function Install-OesFiles([string]$Source, [string]$Root) {
    $Source = Assert-OesLocalRoot $Source
    $Root = Assert-OesLocalRoot $Root
    $manifest = Test-OesManifest $Source
    Get-OesInstallState $Root | Out-Null
    if ($Source -ne $Root) {
        if (Test-Path -LiteralPath $Root) {
            $items = @(Get-ChildItem -LiteralPath $Root -Force)
            if ($items.Count -gt 0 -and -not (Test-Path -LiteralPath (Join-Path $Root 'private/install-state.json'))) {
                throw 'Existing nonempty directory is not an owned OES installation.'
            }
        }
        [IO.Directory]::CreateDirectory((Join-Path $Root 'private')) | Out-Null
        Set-OesPrivateAcl (Join-Path $Root 'private')
        $state = Get-OesInstallState $Root
        Write-OesJson (Join-Path $Root 'private/install-state.json') $state
        foreach ($entry in $manifest.files) {
            $target = Get-OesChildPath $Root $entry.path
            if ($entry.path -eq 'settings.json' -and (Test-Path -LiteralPath $target)) { continue }
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
            [IO.File]::Copy((Get-OesChildPath $Source $entry.path), $target, $true)
        }
        [IO.File]::Copy((Join-Path $Source 'bundle-manifest.json'), (Join-Path $Root 'bundle-manifest.json'), $true)
    }
    foreach ($name in @('private','data')) {
        $dir = Join-Path $Root $name
        [IO.Directory]::CreateDirectory($dir) | Out-Null
        Set-OesPrivateAcl $dir
    }
    Test-OesManifest $Root | Out-Null
}

function Expand-OesZip([string]$Archive, [string]$Destination) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Directory]::CreateDirectory($Destination) | Out-Null
    $zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        $seen = @{}
        foreach ($entry in $zip.Entries) {
            $relative = $entry.FullName.Replace('/', '\')
            if (-not $relative) { continue }
            $path = Get-OesChildPath $Destination $relative
            if (($entry.ExternalAttributes -shr 16 -band 0xf000) -eq 0xa000 -or $seen.ContainsKey($path)) {
                throw 'Unsafe or duplicate archive member.'
            }
            $seen[$path] = $true
            if ($relative.EndsWith('\')) { [IO.Directory]::CreateDirectory($path) | Out-Null; continue }
            # This pinned greenlet wheel also ships C headers. Retain them as vendor
            # metadata; no native compilation or headers lookup occurs at runtime.
            if ($relative -match '\.data\\' -and $relative -notmatch '\.data\\headers\\') {
                throw 'This runtime does not support wheel .data relocation.'
            }
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path)) | Out-Null
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $path, $false)
        }
    } finally { $zip.Dispose() }
}

function Invoke-OesProcess([string]$File, [string[]]$Arguments, [string]$Root,
                           [string]$InputText, [int]$TimeoutSeconds = 600) {
    # Native Windows argument quoting, including trailing backslashes before a quote.
    $quoted = foreach ($value in $Arguments) {
        '"' + [regex]::Replace([regex]::Replace($value, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
    }
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $File
    $info.Arguments = $quoted -join ' '
    $info.WorkingDirectory = $Root
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.RedirectStandardInput = $true
    $info.StandardOutputEncoding = $script:OesUtf8
    $info.StandardErrorEncoding = $script:OesUtf8
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    try {
        if (-not $process.Start()) { throw 'Could not start deployment process.' }
        $out = $process.StandardOutput.ReadToEndAsync()
        $err = $process.StandardError.ReadToEndAsync()
        $writer = [IO.StreamWriter]::new($process.StandardInput.BaseStream, $script:OesUtf8)
        try { if ($null -ne $InputText) { $writer.WriteLine($InputText) } }
        finally { $writer.Dispose() }
        $clock = [Diagnostics.Stopwatch]::StartNew()
        while (-not $process.HasExited) {
            if ($script:OesPumpUi) { & $script:OesPumpUi }
            if ($TimeoutSeconds -gt 0 -and $clock.Elapsed.TotalSeconds -gt $TimeoutSeconds) {
                $process.Kill()
                throw 'Deployment process timeout; no automatic retry.'
            }
            Start-Sleep -Milliseconds 80
        }
        $process.WaitForExit()
        return @{ ExitCode=$process.ExitCode; Stdout=$out.Result; Stderr=$err.Result }
    } finally { $process.Dispose() }
}

function Initialize-OesRuntime([string]$Root, [switch]$Rebuild) {
    if ([Environment]::OSVersion.Version.Major -lt 10 -or -not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64' -or
        $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { throw 'This release requires Windows x64 (Intel/AMD).' }
    $payload = Read-OesJson (Join-Path $Root 'payload/runtime-payload.json')
    $destination = Join-Path $Root 'runtime/python'
    $versionPath = Join-Path $destination 'runtime-installed.json'
    $fingerprint = (Get-FileHash -LiteralPath (Join-Path $Root 'payload/runtime-payload.json')).Hash
    if (Test-Path -LiteralPath $versionPath) {
        if ((Read-OesJson $versionPath).fingerprint -ne $fingerprint) {
            throw 'Runtime version changed; install the new release in a new directory.'
        }
    } else {
        # Interrupted extraction can safely restart by replacing only the dedicated runtime tree.
        if (Test-Path -LiteralPath $destination) {
            $resolved = Assert-OesLocalRoot $destination
            if ($resolved -ne (Get-OesChildPath $Root 'runtime/python')) { throw 'Unsafe runtime cleanup target.' }
            $links = @(Get-ChildItem -LiteralPath $resolved -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
            if ($links.Count) { throw 'Runtime contains reparse points.' }
            Remove-Item -LiteralPath $resolved -Recurse -Force
        }
        foreach ($entry in $payload.files) {
            $path = Get-OesChildPath (Join-Path $Root 'payload') $entry.path
            if ((Get-FileHash -LiteralPath $path).Hash.ToLower() -ne $entry.sha256) { throw 'Runtime payload checksum mismatch.' }
        }
        $pythonZip = @($payload.files | Where-Object { $_.path -like 'python-*-embed-amd64.zip' })
        if ($pythonZip.Count -ne 1 -or $payload.architecture -ne 'AMD64') { throw 'Invalid Python payload.' }
        Expand-OesZip (Join-Path $Root ('payload/' + $pythonZip[0].path)) $destination
        $packages = Join-Path $destination 'Lib/site-packages'
        foreach ($entry in $payload.files | Where-Object { $_.path.EndsWith('.whl') }) {
            Expand-OesZip (Join-Path $Root ('payload/' + $entry.path)) $packages
        }
        $pth = @(Get-ChildItem -LiteralPath $destination -Filter 'python*._pth')
        if ($pth.Count -ne 1) { throw 'Missing embedded Python path contract.' }
        $stdlib = @(Get-ChildItem -LiteralPath $destination -Filter 'python3*.zip')
        if ($stdlib.Count -ne 1) { throw 'Missing embedded standard library.' }
        [IO.File]::WriteAllText($pth[0].FullName,
            ($stdlib[0].Name + "`n.`nLib/site-packages`n../../skills/usql-web-query-operator/scripts`nimport site`n"), $script:OesUtf8)
        Write-OesJson $versionPath @{fingerprint=$fingerprint;python=$payload.python_version}
    }
    $probe = Invoke-OesProcess (Join-Path $destination 'python.exe') @('-c',
        'import ssl,zoneinfo,greenlet,playwright.sync_api,openpyxl,tzdata; from oes_achievement import cli; zoneinfo.ZoneInfo("Asia/Shanghai"); print("runtime_ok")') $Root
    if ($probe.ExitCode -ne 0 -or $probe.Stdout.Trim() -ne 'runtime_ok') {
        if (-not $Rebuild) {
            Remove-Item -LiteralPath (Get-OesChildPath $Root 'runtime/python/runtime-installed.json') -Force
            Initialize-OesRuntime $Root -Rebuild
            return
        }
        throw 'Embedded Python dependency verification failed after rebuilding once.'
    }
}

function Get-OesInstallState([string]$Root) {
    $path = Join-Path $Root 'private/install-state.json'
    if (Test-Path -LiteralPath $path) {
        $state = Read-OesJson $path
        if ($state.owner_sid -ne (Get-OesSid) -or $state.root -ne $Root) {
            throw 'Installation belongs to a different Windows user or path.'
        }
        return $state
    }
    return [PSCustomObject]@{schema_version=1;owner_sid=(Get-OesSid);root=$Root;
        installation_id=[Guid]::NewGuid().ToString('N');task_name=('OES-Base-Sync-' + (Get-OesHash $Root).Substring(0,8));
        status='prepared';stage='files';verification_run_key=('install_' + [Guid]::NewGuid().ToString('N'))}
}

function Save-OesInstallState([string]$Root, $State, [string]$Status, [string]$Stage, [string]$ErrorType) {
    $State.status = $Status
    $State.stage = $Stage
    Write-OesJson (Join-Path $Root 'private/install-state.json') $State
    $logs = Join-Path $Root 'data/installer-logs'
    [IO.Directory]::CreateDirectory($logs) | Out-Null
    $today = [DateTime]::Now.Date
    foreach ($file in Get-ChildItem -LiteralPath $logs -Filter 'installer-*.jsonl') {
        $day = [DateTime]::MinValue
        if ([DateTime]::TryParseExact($file.BaseName.Substring(10), 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture,
                                     [Globalization.DateTimeStyles]::None, [ref]$day) -and $day -lt $today.AddDays(-29)) {
            Remove-Item -LiteralPath $file.FullName -Force
        }
    }
    $event = @{timestamp=[DateTimeOffset]::Now.ToString('o');event='deployment_stage';stage=$Stage;status=$Status}
    if ($ErrorType) { $event.error_type=$ErrorType }
    [IO.File]::AppendAllText((Join-Path $logs ('installer-' + $today.ToString('yyyy-MM-dd') + '.jsonl')),
                            (($event | ConvertTo-Json -Compress) + "`n"), $script:OesUtf8)
}

function Set-OesCredentials([string]$Root, [string]$Username, [string]$Password) {
    if ([string]::IsNullOrWhiteSpace($Username) -or [string]::IsNullOrEmpty($Password) -or
        $Username -match '[\r\n\x00"]' -or $Password -match '[\r\n\x00]') { throw 'Invalid credential input.' }
    $path = Join-Path $Root 'private/usql_api.env'
    $text = '# mi.gaotu100.com OES Web Query (Playwright) credentials' + "`n" +
        'BAIJIA_USERNAME="' + $Username.Trim() + '"' + "`n" + 'BAIJIA_PASSWORD="' + $Password + '"' + "`n"
    $changed = -not (Test-Path -LiteralPath $path)
    if (-not $changed) { $changed = [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8) -ne $text }
    [IO.File]::WriteAllText($path, $text, $script:OesUtf8)
    if ($changed) {
        foreach ($relative in @('data/runtime/oes-achievement/state.json','data/runtime/oes-outlook/state.json',
                               'data/runtime/oes-outlook/state.account')) {
            $statePath = Get-OesChildPath $Root $relative
            if (Test-Path -LiteralPath $statePath) { Remove-Item -LiteralPath $statePath -Force }
        }
    }
}

function Get-OesTaskFolder {
    $service = New-Object -ComObject Schedule.Service
    $service.Connect()
    return $service.GetFolder('\')
}

function Find-OesTask($Folder, [string]$Name) {
    # Enumerate names rather than treating arbitrary COM errors as "not found".
    foreach ($task in $Folder.GetTasks(1)) { if ($task.Name -eq $Name) { return $task } }
    return $null
}

function Assert-OesTaskOwner($Task, $State) {
    $definition = $Task.Definition
    $action = $definition.Actions.Item(1)
    $expected = '"' + (Join-Path $State.root 'skills/usql-web-query-operator/scripts/run_oes_base_silent.py') +
                '" --settings "' + (Join-Path $State.root 'settings.json') + '"'
    $principal=$definition.Principal.UserId
    if ($principal -notmatch '^S-1-') {
        $principal=([Security.Principal.NTAccount]::new($principal)).Translate([Security.Principal.SecurityIdentifier]).Value
    }
    $checks=@{
        source=($definition.RegistrationInfo.Source -eq ('Gaotu.OesBase.' + $State.installation_id));
        principal=($principal -eq $State.owner_sid);count=($definition.Actions.Count -eq 1);
        executable=([IO.Path]::GetFullPath($action.Path) -eq [IO.Path]::GetFullPath((Join-Path $State.root 'runtime/python/pythonw.exe')));
        arguments=($action.Arguments -eq $expected);directory=([IO.Path]::GetFullPath($action.WorkingDirectory) -eq $State.root)
    }
    $drift=@($checks.Keys | Where-Object {-not $checks[$_]})
    if ($drift.Count) {
        throw ('Task identity drifted; refusing to modify: ' + ($drift -join ','))
    }
}

function Suspend-OesTask($State) {
    $folder = Get-OesTaskFolder
    $task = Find-OesTask $folder $State.task_name
    if ($null -ne $task) {
        Assert-OesTaskOwner $task $State
        if ($task.State -in @(2,4)) { throw 'The existing task is running or queued; wait before maintenance.' }
        $task.Enabled = $false
        if ((Find-OesTask $folder $State.task_name).Enabled) { throw 'Failed to disable the owned task.' }
    }
}

function Disable-OesTask($State) {
    $folder = Get-OesTaskFolder
    $task = Find-OesTask $folder $State.task_name
    if ($null -ne $task) {
        Assert-OesTaskOwner $task $State
        # Prevent future launches without terminating an in-flight synchronization.
        $task.Enabled=$false
        if ((Find-OesTask $folder $State.task_name).Enabled) { throw 'Owned task is still enabled.' }
    }
}

function Register-OesTaskDisabled($State) {
    $folder = Get-OesTaskFolder
    $existing = Find-OesTask $folder $State.task_name
    if ($null -ne $existing) { Assert-OesTaskOwner $existing $State; Suspend-OesTask $State }
    $xmlPath = Join-Path $State.root ('task-scheduler/task-' + [Guid]::NewGuid().ToString('N') + '.xml')
    $result = Invoke-OesProcess "$env:SystemRoot/System32/WindowsPowerShell/v1.0/powershell.exe" @(
        '-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $State.root 'prepare-task.ps1'),
        '-BundleRoot',$State.root,'-TaskName',$State.task_name,'-OutputPath',$xmlPath) $State.root
    if ($result.ExitCode -ne 0) { throw 'Task XML generation failed.' }
    $service = New-Object -ComObject Schedule.Service
    $service.Connect()
    $definition = $service.NewTask(0)
    $definition.XmlText = [IO.File]::ReadAllText($xmlPath)
    $definition.RegistrationInfo.Source = 'Gaotu.OesBase.' + $State.installation_id
    $definition.Settings.Enabled = $false
    $flags = 2
    if ($null -ne $existing) { $flags = 6 }
    $folder.RegisterTaskDefinition($State.task_name, $definition, $flags, $State.owner_sid, $null, 3, $null) | Out-Null
    $actual = Find-OesTask $folder $State.task_name
    Assert-OesTaskOwner $actual $State
    if ($actual.Enabled -or -not $actual.Definition.Settings.Hidden -or
        $actual.Definition.Principal.LogonType -ne 3 -or $actual.Definition.Settings.MultipleInstances -ne 2 -or
        $actual.Definition.Triggers.Item(1).Repetition.Interval -ne 'PT30M') { throw 'Native scheduler readback failed.' }
}

function Enable-OesTask($State) {
    $folder = Get-OesTaskFolder
    $task = Find-OesTask $folder $State.task_name
    if ($null -eq $task) { throw 'Owned task is not registered.' }
    Assert-OesTaskOwner $task $State
    $task.Enabled = $true
    if (-not (Find-OesTask $folder $State.task_name).Enabled) { throw 'Failed to enable the owned task.' }
}

function Remove-OesTask($State) {
    Suspend-OesTask $State
    $folder = Get-OesTaskFolder
    $task = Find-OesTask $folder $State.task_name
    if ($null -ne $task) { Assert-OesTaskOwner $task $State; $folder.DeleteTask($State.task_name, 0) }
    if ($null -ne (Find-OesTask $folder $State.task_name)) { throw 'Owned task removal failed.' }
}

function Assert-OesSyncReceipt([string]$Root, $Settings, [string]$RunKey) {
    $hash = Get-OesHash $RunKey
    $path = Join-Path $Root ('data/runs/base-sync-' + $hash.Substring(0,24) + '/base-receipt.json')
    $receipt = Read-OesJson $path
    if ($receipt.status -ne 'completed' -or $receipt.identity.run_key_hash -ne $hash -or
        $receipt.identity.base_token -ne $Settings.base_token -or $receipt.identity.table_id -ne $Settings.table_id -or
        $receipt.identity.config_table_id -ne $Settings.config_table_id -or
        $receipt.identity.config_record_id -ne $Settings.config_record_id -or
        $receipt.verification.verified -ne $true -or @($receipt.verification.fields_verified).Count -ne 13 -or
        $receipt.verification.mismatch_count -ne 0 -or $receipt.row_count -ne $receipt.verification.row_count) {
        throw 'First synchronization did not prove complete 13-field replacement.'
    }
    return $receipt
}

function Get-OesTargetCoordinates([string]$Url) {
    $uri = [Uri]$Url.Trim()
    if ($uri.Scheme -ne 'https' -or $uri.Host -notmatch '(^|\.)feishu\.cn$' -or
        $uri.AbsolutePath -notmatch '^/base/([A-Za-z0-9]+)$') { throw 'Invalid Base URL.' }
    $baseToken = $Matches[1]
    $query = [regex]::Match($uri.Query,'(?:^\?|&)table=(tbl[A-Za-z0-9]+)(?:&|$)')
    if (-not $query.Success) { throw 'Base URL must include the target table.' }
    return @{base_token=$baseToken;table_id=$query.Groups[1].Value}
}

function New-OesVerificationIfCompleted([string]$Root, $State, $Settings) {
    $runHash = Get-OesHash $State.verification_run_key
    $name = 'base-sync-' + $runHash.Substring(0,24)
    $targetHash = (Get-OesHash ($Settings.base_token + ':' + $Settings.table_id)).Substring(0,24)
    foreach ($relative in @(('data/runs/' + $name + '/base-receipt.json'),
                            ('data/runtime/completed-runs/' + $targetHash + '/' + $name + '.json'))) {
        $path = Join-Path $Root $relative
        if (Test-Path -LiteralPath $path) {
            $completed = Read-OesJson $path
            if ($completed.status -eq 'completed' -and $completed.identity.run_key_hash -eq $runHash -and
                $completed.verification.verified -eq $true -and $completed.verification.mismatch_count -eq 0) {
                $State.verification_run_key='install_' + [Guid]::NewGuid().ToString('N')
                return
            }
        }
    }
    # Failed or ambiguous attempts retain their original key and are never bypassed.
}

function Invoke-OesDeployment([string]$Source, $Options, [scriptblock]$Progress,
        [scriptblock]$Browser, [scriptblock]$Authorization, [scriptblock]$Job, [scriptblock]$Power) {
    $root = Assert-OesLocalRoot $Options.root
    $target = Get-OesTargetCoordinates $Options.base_url
    if ($Options.config_table_id -notmatch '^tbl[A-Za-z0-9]+$' -or
        $Options.config_record_id -notmatch '^rec[A-Za-z0-9]+$' -or -not $Options.confirm_replace) {
        throw 'Reviewed target replacement and configuration identities are required.'
    }
    $mutex = [Threading.Mutex]::new($false, ('Local\Gaotu.OesInstall.' + (Get-OesHash $root).Substring(0,24)))
    $locked=$false; $state=$null; $currentStage='files'
    try {
        try { $locked=$mutex.WaitOne(0) }
        catch [Threading.AbandonedMutexException] { $locked=$true }
        if (-not $locked) { throw 'Another installer is already maintaining this directory.' }
        & $Progress $currentStage
        Test-OesManifest $Source | Out-Null
        $state=Get-OesInstallState $root
        Suspend-OesTask $state
        Install-OesFiles $Source $root
        $state=Get-OesInstallState $root
        Save-OesInstallState $root $state 'installing' 'files'
        $currentStage='runtime'; & $Progress $currentStage
        Initialize-OesRuntime $root
        $settings=Read-OesJson (Join-Path $root 'settings.json')
        & $Browser $root $settings
        $currentStage='configuration'; & $Progress $currentStage
        if (($settings.base_token -ne $target.base_token -or $settings.table_id -ne $target.table_id -or
            $settings.config_table_id -ne $Options.config_table_id -or $settings.config_record_id -ne $Options.config_record_id) -and
            (Test-Path -LiteralPath (Join-Path $root 'data/runs'))) {
            throw 'Target identity changed; use a new installation directory.'
        }
        $settings.base_token=$target.base_token; $settings.table_id=$target.table_id
        $settings.config_table_id=$Options.config_table_id; $settings.config_record_id=$Options.config_record_id
        $settings | Add-Member -NotePropertyName lark_profile -NotePropertyValue ('oes-base-' + $state.installation_id.Substring(0,16)) -Force
        if ($Options.password) { Set-OesCredentials $root $Options.username $Options.password }
        else {
            $file=Join-Path $root 'private/usql_api.env'
            if (-not (Test-Path -LiteralPath $file)) { throw 'First-time account requires password.' }
            $account=[regex]::Match([IO.File]::ReadAllText($file,[Text.Encoding]::UTF8),'(?m)^BAIJIA_USERNAME="?(.*?)"?\r?$')
            if (-not $account.Success -or $account.Groups[1].Value -ne $Options.username.Trim()) {
                throw 'Changed account requires password.'
            }
        }
        New-OesVerificationIfCompleted $root $state $settings
        Write-OesJson (Join-Path $root 'settings.json') $settings
        Save-OesInstallState $root $state 'installing' 'configuration'
        $currentStage='feishu'; & $Progress $currentStage
        & $Authorization $root $settings
        Save-OesInstallState $root $state 'installing' 'feishu'
        $currentStage='oes'; & $Progress $currentStage
        & $Job $root 'login'
        Save-OesInstallState $root $state 'installing' 'oes'
        $currentStage='mail'; & $Progress $currentStage
        & $Job $root 'mail-login'
        & $Job $root 'check'
        Save-OesInstallState $root $state 'installing' 'mail'
        $currentStage='sync'; & $Progress $currentStage
        $sync=Invoke-OesProcess (Join-Path $root 'runtime/python/pythonw.exe') @(
            (Join-Path $root 'skills/usql-web-query-operator/scripts/run_oes_base_silent.py'),
            '--settings',(Join-Path $root 'settings.json'),'--run-key',$state.verification_run_key) $root $null 0
        if ($sync.ExitCode -ne 0) { throw 'Full sync failed; preserve its recovery receipt.' }
        $receipt=Assert-OesSyncReceipt $root $settings $state.verification_run_key
        Save-OesInstallState $root $state 'verified' 'sync'
        $currentStage='scheduler'; & $Progress $currentStage
        Register-OesTaskDisabled $state
        if ($Options.power) { & $Power $root $state 'Apply' }
        $final='disabled'
        if ($Options.activate) { Enable-OesTask $state; $final='active' }
        Save-OesInstallState $root $state $final 'complete'
        return @{root=$root;task_name=$state.task_name;status=$final;row_count=$receipt.row_count}
    } catch {
        if ($locked -and $null -ne $state -and (Test-Path -LiteralPath (Join-Path $root 'private/install-state.json'))) {
            Disable-OesTask $state
            Save-OesInstallState $root $state 'failed' $currentStage $_.Exception.GetType().Name
        }
        throw
    } finally {
        if ($locked) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
}
