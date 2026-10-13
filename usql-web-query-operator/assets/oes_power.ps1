param(
    [ValidateSet('Plan','Apply','Restore')][string]$Mode = 'Plan',
    [Parameter(Mandatory=$true)][string]$Root,
    [string]$ExpectedSid
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'installer/core.ps1')
$Root = Assert-OesLocalRoot $Root
if (-not ('OesPower.Native' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace OesPower {
    public static class Native {
        [DllImport("powrprof.dll")] public static extern uint PowerGetActiveScheme(IntPtr key, out IntPtr scheme);
        [DllImport("powrprof.dll")] public static extern uint PowerReadACValueIndex(IntPtr key, ref Guid scheme, ref Guid sub, ref Guid setting, out uint value);
        [DllImport("powrprof.dll")] public static extern uint PowerReadDCValueIndex(IntPtr key, ref Guid scheme, ref Guid sub, ref Guid setting, out uint value);
        [DllImport("kernel32.dll")] public static extern IntPtr LocalFree(IntPtr pointer);
    }
}
'@
}

function Get-OesPowerSnapshot {
    $pointer = [IntPtr]::Zero
    if ([OesPower.Native]::PowerGetActiveScheme([IntPtr]::Zero, [ref]$pointer) -ne 0) { throw 'Cannot read active power scheme.' }
    try { $scheme = [Guid][Runtime.InteropServices.Marshal]::PtrToStructure($pointer, [type][Guid]) }
    finally { [OesPower.Native]::LocalFree($pointer) | Out-Null }
    $entries = @()
    foreach ($spec in @(
        @('238c9fa8-0aad-41ed-83f4-97be242c8f20','29f6c1db-86da-48c5-9fdb-f2b67b1f44da','sleep'),
        @('238c9fa8-0aad-41ed-83f4-97be242c8f20','9d7815a6-7ee4-497e-8888-515a05f02364','hibernate'),
        @('4f971e89-eebd-4455-a8de-9e59040e7347','5ca83367-6e45-459f-a27b-476b1d01c936','lid')
    )) {
        $sub = [Guid]$spec[0]; $setting = [Guid]$spec[1]; [uint32]$ac = 0; [uint32]$dc = 0
        $acCode = [OesPower.Native]::PowerReadACValueIndex([IntPtr]::Zero,[ref]$scheme,[ref]$sub,[ref]$setting,[ref]$ac)
        $dcCode = [OesPower.Native]::PowerReadDCValueIndex([IntPtr]::Zero,[ref]$scheme,[ref]$sub,[ref]$setting,[ref]$dc)
        if ($acCode -ne 0 -or $dcCode -ne 0) {
            if ($spec[2] -eq 'lid') { continue }
            throw 'Cannot read required power setting.'
        }
        $entries += @{sub=$spec[0];setting=$spec[1];name=$spec[2];ac=$ac;dc=$dc}
    }
    $global = Get-ItemProperty -LiteralPath 'HKLM:/SYSTEM/CurrentControlSet/Control/Power'
    return @{scheme=$scheme.ToString();settings=$entries;hibernate_enabled=[int]$global.HibernateEnabled;
             hibernate_type=[int]$global.HiberFileType}
}

function Invoke-OesPowerCfg([string[]]$Arguments) {
    & "$env:SystemRoot/System32/powercfg.exe" @Arguments | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'A required powercfg operation was rejected.' }
}

function Set-OesPowerSnapshot($Snapshot, [bool]$Disable) {
    foreach ($entry in $Snapshot.settings) {
        $ac = $entry.ac; $dc = $entry.dc
        if ($Disable) { $ac = 0; $dc = 0 }
        Invoke-OesPowerCfg @('/setacvalueindex',$Snapshot.scheme,$entry.sub,$entry.setting,[string]$ac)
        Invoke-OesPowerCfg @('/setdcvalueindex',$Snapshot.scheme,$entry.sub,$entry.setting,[string]$dc)
    }
    Invoke-OesPowerCfg @('/setactive',$Snapshot.scheme)
    if ($Disable -or $Snapshot.hibernate_enabled -eq 0) { Invoke-OesPowerCfg @('/hibernate','off') }
    else {
        Invoke-OesPowerCfg @('/hibernate','on')
        # HiberFileType: 0=none, 1=reduced, 2=full.
        if ($Snapshot.hibernate_type -eq 1) { Invoke-OesPowerCfg @('/hibernate','/type','reduced') }
        elseif ($Snapshot.hibernate_type -eq 2) { Invoke-OesPowerCfg @('/hibernate','/type','full') }
    }
}

function Assert-OesPowerCompatible($Original, $Current) {
    if ($Original.scheme -ne $Current.scheme -or
        $Current.hibernate_enabled -notin @(0,$Original.hibernate_enabled)) { throw 'Power configuration drifted.' }
    if ($Original.hibernate_enabled -ne 0 -and
        $Current.hibernate_type -notin @(0,$Original.hibernate_type)) { throw 'Hibernation type drifted.' }
    foreach ($entry in $Original.settings) {
        $actual=@($Current.settings | Where-Object { $_.setting -eq $entry.setting -and $_.sub -eq $entry.sub })
        if ($actual.Count -ne 1 -or $actual[0].ac -notin @(0,$entry.ac) -or $actual[0].dc -notin @(0,$entry.dc)) {
            throw 'Power values drifted independently from the recorded operation.'
        }
    }
}

$plan = Get-OesPowerSnapshot
if ($Mode -eq 'Plan') {
    @{status='read_only_plan';power_settings_changed=$false;current=$plan} | ConvertTo-Json -Depth 8
    exit 0
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Power changes require elevation.'
}
$state = Read-OesJson (Join-Path $Root 'private/install-state.json')
if (-not $ExpectedSid -or $state.owner_sid -ne $ExpectedSid -or $state.root -ne $Root) { throw 'Invalid installation owner.' }
$backupPath = Join-Path $Root 'private/power-before.json'
$receiptPath = Join-Path $Root 'private/power-result.json'
try {
    if ($Mode -eq 'Apply') {
        if (Test-Path -LiteralPath $backupPath) {
            $backup = Read-OesJson $backupPath
            if ($backup.installation_id -ne $state.installation_id -or $backup.original.scheme -ne $plan.scheme) {
                throw 'Original power backup or active scheme changed; refusing to overwrite backup.'
            }
            Assert-OesPowerCompatible $backup.original $plan
        } else {
            $backup = @{installation_id=$state.installation_id;owner_sid=$ExpectedSid;original=$plan;status='prepared'}
            Write-OesJson $backupPath $backup
            Invoke-OesPowerCfg @('/export',(Join-Path $Root 'private/power-before.pow'),$plan.scheme)
        }
        Set-OesPowerSnapshot $backup.original $true
        $after = Get-OesPowerSnapshot
        if ($after.hibernate_enabled -ne 0 -or @($after.settings | Where-Object { $_.ac -ne 0 -or $_.dc -ne 0 }).Count) {
            throw 'Power setting readback failed.'
        }
        Write-OesJson $receiptPath @{status='applied';installation_id=$state.installation_id;scheme=$plan.scheme;verified=$true}
    } else {
        $backup = Read-OesJson $backupPath
        if ($backup.installation_id -ne $state.installation_id -or $backup.owner_sid -ne $ExpectedSid -or
            $backup.original.scheme -ne $plan.scheme) { throw 'Backup identity or active scheme drifted.' }
        # Do not overwrite independent changes made after this installer.
        Assert-OesPowerCompatible $backup.original $plan
        Set-OesPowerSnapshot $backup.original $false
        $restored = Get-OesPowerSnapshot
        foreach ($original in $backup.original.settings) {
            $actual = @($restored.settings | Where-Object { $_.setting -eq $original.setting })
            if ($actual.Count -ne 1 -or $actual[0].ac -ne $original.ac -or $actual[0].dc -ne $original.dc) {
                throw 'Power restoration readback failed.'
            }
        }
        if ($restored.hibernate_enabled -ne $backup.original.hibernate_enabled) { throw 'Hibernation restoration failed.' }
        if ($backup.original.hibernate_enabled -ne 0 -and $restored.hibernate_type -ne $backup.original.hibernate_type) {
            throw 'Hibernation type restoration failed.'
        }
        Write-OesJson $receiptPath @{status='restored';installation_id=$state.installation_id;verified=$true}
    }
} catch {
    Write-OesJson $receiptPath @{status='failed';installation_id=$state.installation_id;verified=$false;error_type=$_.Exception.GetType().Name}
    exit 2
}
