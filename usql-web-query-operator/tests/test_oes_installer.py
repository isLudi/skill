"""Installer tests: native UI/XML, isolated files, mocked scheduler/power/remote writes."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from _shared.env import read_env_section
from oes_achievement.base_client import BaseClient
import build_oes_deployment as builder
from prepare_oes_runtime import fetch as prepare_runtime_fetch

TEST_ROOT = SKILL.parents[1] / "runtime/oes-installer-tests"


class InstallerTestCase(unittest.TestCase):
    def setUp(self):
        TEST_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEST_ROOT)
        self.root = Path(self.temp.name)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        assert self.root.resolve().parent == TEST_ROOT.resolve()
        for attempt in range(30):
            try:
                self.temp.cleanup()
                return
            except OSError:
                if attempt == 29:
                    raise
                time.sleep(0.1)

    def powershell(self, source, **environment):
        fixture = self.root / "fixture.ps1"
        fixture.write_text(source, encoding="utf-8")
        env = dict(os.environ, OES_FIXTURE=str(fixture), OES_CORE=str(SKILL / "assets/oes_install_core.ps1"),
                   OES_TEST_ROOT=str(self.root), OES_TEST_PYTHON=sys.executable, OES_SKILL=str(SKILL), **environment)
        # PS 5.1 otherwise interprets non-BOM source as the legacy ANSI codepage.
        result = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
            "& ([ScriptBlock]::Create([IO.File]::ReadAllText($env:OES_FIXTURE,[Text.Encoding]::UTF8)))"],
            env=env, capture_output=True, encoding="utf-8", timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)


class CredentialsAndProfileTests(InstallerTestCase):
    def test_runtime_payload_rejects_repository_root(self):
        with self.assertRaisesRegex(ValueError, "outside the skills repository"):
            prepare_runtime_fetch(SKILL.parent)

    def test_quoted_secret_preserves_whitespace_quotes_and_other_sections(self):
        path = self.root / "private.env"
        password = '  "single\'quote and backslash\\"  '
        path.write_text('# other\nBAIJIA_PASSWORD=wrong\n# exact\nBAIJIA_PASSWORD="' + password + '"\n', encoding="utf-8")
        self.assertEqual(read_env_section(path, "exact")["BAIJIA_PASSWORD"], password)

    def test_named_profile_is_explicit_for_shortcut_and_native_requests(self):
        client = BaseClient("BaseToken", self.root, sys.executable)
        success = subprocess.CompletedProcess([], 0, stdout=json.dumps({"ok": True, "identity": "user", "data": {}}))
        with patch.dict(os.environ, {"OES_LARK_PROFILE": "oes-base-fixture"}), \
             patch("oes_achievement.base_client.subprocess.run", return_value=success) as run:
            client.call("+field-list")
            self.assertEqual(run.call_args.args[0][1:3], ["--profile", "oes-base-fixture"])
            client.native("tblFixture", "batch_create", {"records": []})
            self.assertEqual(run.call_args.args[0][1:3], ["--profile", "oes-base-fixture"])
            self.assertFalse(run.call_args.kwargs["shell"])
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(client.argv("api"), [client.executable, "api"])

    def test_builder_rejects_secret_profiles_and_preserves_existing_directory(self):
        payload=self.root / "payload"
        payload.mkdir()
        entries=[]
        for relative in [f"python-{builder.PYTHON_VERSION}-embed-amd64.zip", *("wheels/" + item[2] for item in builder.WHEELS)]:
            path=payload / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"isolated-fixture")
            source=(f"https://www.python.org/ftp/python/{builder.PYTHON_VERSION}/{relative}"
                    if relative.endswith(".zip") else f"https://files.pythonhosted.org/packages/fixture/{Path(relative).name}")
            entries.append({"path":relative,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"source":source})
        (payload / "runtime-payload.json").write_text(json.dumps({"python_version":builder.PYTHON_VERSION,
            "architecture":"AMD64","files":entries}), encoding="utf-8")
        profile=json.loads((SKILL / "assets/oes_installer_profile.json").read_text(encoding="utf-8"))
        profile["app_secret"]="must-not-be-distributed"
        custom=self.root / "profile.json"
        custom.write_text(json.dumps(profile), encoding="utf-8")
        output=self.root / "bundle"
        with patch.object(builder,"PYTHON_SHA256",entries[0]["sha256"]):
            with self.assertRaisesRegex(ValueError,"public coordinates"):
                builder.build(output,Path(sys.executable),payload,custom)
            profile=json.loads((SKILL / "assets/oes_installer_profile.json").read_text(encoding="utf-8"))
            profile["browser_channel"]="must-not-be-packaged"
            custom.write_text(json.dumps(profile), encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"browser channel"):
                builder.build(output,Path(sys.executable),payload,custom)
            profile["browser_channel"]="msedge"
            profile["mail_wait_seconds"]="credential-shaped-value"
            custom.write_text(json.dumps(profile), encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"numeric setting"):
                builder.build(output,Path(sys.executable),payload,custom)
            manifest=json.loads((payload / "runtime-payload.json").read_text(encoding="utf-8"))
            manifest["files"][1]["source"] += "?token=synthetic-secret"
            (payload / "runtime-payload.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"manifest contains an invalid source"):
                builder.build(output,Path(sys.executable),payload)
        self.assertFalse(output.exists())
        output.mkdir()
        keep=output / "keep.txt"
        keep.write_text("owned-by-user", encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"existing contents"):
            builder.build(output,Path(sys.executable),payload)
        self.assertEqual(keep.read_text(encoding="utf-8"),"owned-by-user")


@unittest.skipUnless(os.name == "nt", "Windows installer")
class WindowsInstallerTests(InstallerTestCase):
    def test_power_commands_are_mocked_and_partial_restore_preserves_prior_values(self):
        result = self.powershell(r'''
. $env:OES_CORE
$tokens=$null; $parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $env:OES_SKILL 'assets/oes_power.ps1'),[ref]$tokens,[ref]$parseErrors)
if ($parseErrors.Count) {throw 'Power syntax error'}
# Load functions only: no live Apply, registry change, powercfg or elevation.
foreach ($node in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)) {
    . ([ScriptBlock]::Create($node.Extent.Text))
}
$script:commands=@()
function Invoke-OesPowerCfg($Arguments) { $script:commands+=,@($Arguments) }
$original=@{scheme='fixture';hibernate_enabled=1;hibernate_type=2;
    settings=@(@{sub='sub';setting='setting';ac=900;dc=600})}
$partial=@{scheme='fixture';hibernate_enabled=1;hibernate_type=0;settings=@(@{sub='sub';setting='setting';ac=0;dc=600})}
Assert-OesPowerCompatible $original $partial
Set-OesPowerSnapshot $original $false
if ($script:commands[0][4] -ne '900' -or $script:commands[1][4] -ne '600' -or
    ($script:commands[3] -join ' ') -ne '/hibernate on') {throw 'Original power values were not restored'}
$script:commands=@()
Set-OesPowerSnapshot $original $true
if ($script:commands[0][4] -ne '0' -or $script:commands[1][4] -ne '0' -or
    ($script:commands[3] -join ' ') -ne '/hibernate off') {throw 'Anti-sleep contract changed'}
$partial.settings[0].dc=123
$blocked=$false
try { Assert-OesPowerCompatible $original $partial } catch {$blocked=$true}
if (-not $blocked) {throw 'Independent change overwritten'}
$typeDrift=@{scheme='fixture';hibernate_enabled=1;hibernate_type=1;settings=@(@{sub='sub';setting='setting';ac=0;dc=600})}
$blocked=$false
try { Assert-OesPowerCompatible $original $typeDrift } catch {$blocked=$true}
if (-not $blocked) {throw 'Independent hibernation type change overwritten'}
@{partial_restore=$true;drift_blocked=$true;real_power_changed=$false} | ConvertTo-Json
''')
        self.assertTrue(result["partial_restore"])
        self.assertTrue(result["drift_blocked"])
        self.assertFalse(result["real_power_changed"])

    def test_utf8_secret_via_stdin_is_not_in_argv_or_log(self):
        input_path = self.root / "input.json"
        input_path.write_text(json.dumps({"secret": '模拟秘密$`"\\结束', "argument": '中文 spaced \\'}, ensure_ascii=False), encoding="utf-8")
        result = self.powershell(r'''
. $env:OES_CORE
$inputValue=Read-OesJson (Join-Path $env:OES_TEST_ROOT 'input.json')
$result=Invoke-OesProcess $env:OES_TEST_PYTHON @('-c',
    'import json,sys; print(json.dumps({"arg":sys.argv[1],"stdin":sys.stdin.read().rstrip("\r\n")}))',
    $inputValue.argument) $env:OES_TEST_ROOT $inputValue.secret
$body=$result.Stdout | ConvertFrom-Json
if ($result.ExitCode -ne 0 -or $body.arg -ne $inputValue.argument -or $body.stdin -ne $inputValue.secret) { throw 'UTF8 transport failed' }
@{matched=$true} | ConvertTo-Json
''')
        self.assertTrue(result["matched"])

    def test_credential_change_clears_only_sessions_and_private_acl(self):
        result = self.powershell(r'''
. $env:OES_CORE
$root=$env:OES_TEST_ROOT
[IO.Directory]::CreateDirectory((Join-Path $root 'private')) | Out-Null
Set-OesPrivateAcl (Join-Path $root 'private')
$keep=Join-Path $root 'data/runs/recovery.json'
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($keep)) | Out-Null
[IO.File]::WriteAllText($keep,'recovery')
foreach ($relative in @('data/runtime/oes-achievement/state.json','data/runtime/oes-outlook/state.json','data/runtime/oes-outlook/state.account')) {
    $path=Get-OesChildPath $root $relative
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path)) | Out-Null
    [IO.File]::WriteAllText($path,'state')
}
Set-OesCredentials $root 'account-fixture' 'synthetic-secret'
$acl=[IO.Directory]::GetAccessControl((Join-Path $root 'private'))
$allowed=@((Get-OesSid),'S-1-5-18','S-1-5-32-544')
$unexpected=@($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]) | Where-Object {$_.IdentityReference.Value -notin $allowed})
if ($unexpected.Count -or -not $acl.AreAccessRulesProtected -or -not (Test-Path -LiteralPath $keep)) { throw 'Privacy/recovery regression' }
if (Test-Path -LiteralPath (Join-Path $root 'data/runtime/oes-achievement/state.json')) { throw 'Old state retained' }
$state=Get-OesInstallState $root
Save-OesInstallState $root $state 'prepared' 'configuration'
$logs=Get-ChildItem -LiteralPath (Join-Path $root 'data/installer-logs') -Filter '*.jsonl'
if ([IO.File]::ReadAllText($logs[0].FullName).Contains('synthetic-secret')) { throw 'Secret in logs' }
@{private=$true;recovery_preserved=$true} | ConvertTo-Json
''')
        self.assertTrue(result["private"])
        self.assertTrue(result["recovery_preserved"])

    def test_paths_targets_and_zip_traversal_are_rejected(self):
        bad_zip = self.root / "unsafe.zip"
        with zipfile.ZipFile(bad_zip, "w") as archive:
            archive.writestr("../escaped.txt", "forbidden")
        result = self.powershell(r'''
. $env:OES_CORE
$blocked=0
foreach ($relative in @('../outside','C:\outside','data/../../outside')) {
    try { Get-OesChildPath $env:OES_TEST_ROOT $relative | Out-Null } catch { $blocked++ }
}
foreach ($url in @('https://feishu.cn.evil.test/base/abc?table=tblX','http://x.feishu.cn/base/abc?table=tblX','https://x.feishu.cn/base/abc')) {
    try { Get-OesTargetCoordinates $url | Out-Null } catch { $blocked++ }
}
try { Expand-OesZip (Join-Path $env:OES_TEST_ROOT 'unsafe.zip') (Join-Path $env:OES_TEST_ROOT 'extract') } catch { $blocked++ }
if ($blocked -ne 7 -or (Test-Path -LiteralPath (Join-Path $env:OES_TEST_ROOT 'escaped.txt'))) { throw 'Unsafe path accepted' }
$good=Get-OesTargetCoordinates 'https://gaotuedu.feishu.cn/base/abc?table=tblX&view=vewX'
@{blocked=$blocked;parsed=($good.table_id -eq 'tblX')} | ConvertTo-Json
''')
        self.assertEqual(result["blocked"], 7)
        self.assertTrue(result["parsed"])

    def test_only_completed_verification_rotates_including_purged_cache(self):
        result = self.powershell(r'''
. $env:OES_CORE
$root=$env:OES_TEST_ROOT
$settings=@{base_token='Base';table_id='tblFixture'}
$state=Get-OesInstallState $root
$original=$state.verification_run_key
$hash=Get-OesHash $original
$name='base-sync-' + $hash.Substring(0,24)
$file=Join-Path $root ('data/runs/' + $name + '/base-receipt.json')
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($file)) | Out-Null
Write-OesJson $file @{status='export_uncertain';identity=@{run_key_hash=$hash}}
New-OesVerificationIfCompleted $root $state $settings
if ($state.verification_run_key -ne $original) { throw 'Uncertain key bypassed' }
$index=Join-Path $root ('data/runtime/completed-runs/' + (Get-OesHash 'Base:tblFixture').Substring(0,24) + '/' + $name + '.json')
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($index)) | Out-Null
Write-OesJson $index @{status='completed';identity=@{run_key_hash=$hash};verification=@{verified=$true;mismatch_count=0};cache_state='purged'}
New-OesVerificationIfCompleted $root $state $settings
if ($state.verification_run_key -eq $original) { throw 'Completed repair cannot start fresh' }
@{uncertain_preserved=$true;purged_completed_rotated=$true} | ConvertTo-Json
''')
        self.assertTrue(result["uncertain_preserved"])
        self.assertTrue(result["purged_completed_rotated"])

    def test_pipeline_gates_activation_and_preserves_failed_key(self):
        result = self.powershell(r'''
. $env:OES_CORE
function Test-OesManifest($Root) { return @{} }
function Suspend-OesTask($State) {}
function Disable-OesTask($State) { $script:disabled++ }
function Register-OesTaskDisabled($State) { $script:registered++ }
function Enable-OesTask($State) { $script:enabled++ }
function Initialize-OesRuntime($Root) {}
function Install-OesFiles($Source,$Root) {
    [IO.Directory]::CreateDirectory((Join-Path $Root 'private')) | Out-Null
    $state=Get-OesInstallState $Root
    Write-OesJson (Join-Path $Root 'private/install-state.json') $state
    Copy-Item -LiteralPath (Join-Path $env:OES_SKILL 'assets/oes_installer_profile.json') -Destination (Join-Path $Root 'settings.json')
}
function Invoke-OesProcess($File,$Arguments,$Root,$InputText,$TimeoutSeconds) {
    if ($script:scenario -eq 'write_failure') { return @{ExitCode=2} }
    if ($script:scenario -ne 'no_receipt') {
        $state=Get-OesInstallState $Root
        $settings=Read-OesJson (Join-Path $Root 'settings.json')
        $hash=Get-OesHash $state.verification_run_key
        $file=Join-Path $Root ('data/runs/base-sync-' + $hash.Substring(0,24) + '/base-receipt.json')
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($file)) | Out-Null
        Write-OesJson $file @{status='completed';identity=@{run_key_hash=$hash;base_token=$settings.base_token;
            table_id=$settings.table_id;config_table_id=$settings.config_table_id;config_record_id=$settings.config_record_id};
            row_count=2;verification=@{verified=$true;mismatch_count=0;row_count=2;fields_verified=@(1..13)}}
    }
    return @{ExitCode=0}
}
$report=@()
foreach ($scenario in @('success','no_receipt','write_failure','auth_failure','power_failure')) {
    $script:scenario=$scenario; $script:registered=0; $script:enabled=0; $script:disabled=0
    $root=Join-Path $env:OES_TEST_ROOT $scenario
    $options=@{root=$root;base_url='https://gaotuedu.feishu.cn/base/PVxtbmW3mahfErssCJKcjjwTnVc?table=tbldVzfsawwH5a1A';
        config_table_id='tblNbyMBV97sdHR1';config_record_id='recvx4baH9gZPz';username='account-fixture';
        password='synthetic-secret';confirm_replace=$true;activate=$true;power=$true}
    $failed=$false
    try {
        Invoke-OesDeployment $env:OES_TEST_ROOT $options {} {} `
          {param($r,$s) if($script:scenario -eq 'auth_failure'){throw 'synthetic-secret-raw-error'}} {} `
          {param($r,$s,$m) if($script:scenario -eq 'power_failure'){throw 'denied'}} | Out-Null
    } catch { $failed=$true; $failureMessage=$_.Exception.Message }
    $state=Get-OesInstallState $root
    if ($scenario -eq 'success') {
        if ($failed -or $script:registered -ne 1 -or $script:enabled -ne 1 -or $state.status -ne 'active') { throw ('Success gate failed: ' + $failureMessage) }
    } else {
        if (-not $failed -or $script:enabled -ne 0 -or $state.status -ne 'failed' -or $script:disabled -ne 1) { throw 'Failure activated task' }
        if ($scenario -ne 'power_failure' -and $script:registered -ne 0) { throw 'Registered before verification' }
    }
    if ($scenario -eq 'write_failure') {
        $key=$state.verification_run_key
        try { Invoke-OesDeployment $env:OES_TEST_ROOT $options {} {} {} {} {} | Out-Null } catch {}
        if ((Get-OesInstallState $root).verification_run_key -ne $key) { throw 'Failed write key changed' }
    }
    $logs=Get-ChildItem -LiteralPath (Join-Path $root 'data/installer-logs') -Filter '*.jsonl'
    if ([IO.File]::ReadAllText($logs[0].FullName).Contains('synthetic-secret')) { throw 'Secret logged' }
    $report+=@{scenario=$scenario;passed=$true}
}
$report | ConvertTo-Json
''')
        self.assertEqual(len(result), 5)
        self.assertTrue(all(item["passed"] for item in result))

    def test_native_definition_lifecycle_uses_mock_registry_and_preserves_foreign_task(self):
        result = self.powershell(r'''
. $env:OES_CORE
$root=$env:OES_TEST_ROOT
foreach ($relative in @('runtime/python/pythonw.exe','settings.json','skills/usql-web-query-operator/scripts/run_oes_base_silent.py')) {
    $path=Join-Path $root $relative
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path)) | Out-Null
    if ($relative.EndsWith('pythonw.exe')) { Copy-Item -LiteralPath ([IO.Path]::Combine([IO.Path]::GetDirectoryName($env:OES_TEST_PYTHON),'pythonw.exe')) -Destination $path }
    else { [IO.File]::WriteAllText($path,'fixture') }
}
[IO.Directory]::CreateDirectory((Join-Path $root 'task-scheduler')) | Out-Null
Copy-Item -LiteralPath (Join-Path $env:OES_SKILL 'assets/oes_task_template.xml') -Destination (Join-Path $root 'task-scheduler/task-template.xml')
Copy-Item -LiteralPath (Join-Path $env:OES_SKILL 'assets/oes_prepare_task.ps1') -Destination (Join-Path $root 'prepare-task.ps1')
$script:fakeTask=$null; $script:creates=0; $script:deletes=0
$script:fakeFolder=[PSCustomObject]@{}
$script:fakeFolder | Add-Member ScriptMethod GetTasks {param($flags) if ($script:fakeTask) {return $script:fakeTask}}
$script:fakeFolder | Add-Member ScriptMethod RegisterTaskDefinition {
    param($name,$definition,$flags,$sid,$password,$logon,$sddl)
    if ($flags -ne 2 -or $password -or $logon -ne 3) {throw 'Bad registration contract'}
    $script:creates++
    $script:fakeTask=[PSCustomObject]@{Name=$name;Definition=$definition;Enabled=$false;State=3}
    return $script:fakeTask
}
$script:fakeFolder | Add-Member ScriptMethod DeleteTask {param($name,$flags) $script:deletes++; $script:fakeTask=$null}
function Get-OesTaskFolder { return $script:fakeFolder }
$state=Get-OesInstallState $root
Register-OesTaskDisabled $state
if ($script:fakeTask.Enabled -or $script:creates -ne 1) {throw 'Task enabled before acceptance'}
Enable-OesTask $state
$oldSource=$script:fakeTask.Definition.RegistrationInfo.Source
$script:fakeTask.Definition.RegistrationInfo.Source='different-owner'
$blocked=$false
try { Remove-OesTask $state } catch { $blocked=$true }
if (-not $blocked -or $script:deletes -ne 0 -or -not $script:fakeTask.Enabled) {throw 'Foreign task altered'}
$script:fakeTask.Definition.RegistrationInfo.Source=$oldSource
$script:fakeTask.State=4
Disable-OesTask $state
if ($script:fakeTask.Enabled -or $script:fakeTask.State -ne 4) {throw 'Pause terminated running job'}
$script:fakeTask.State=3
Remove-OesTask $state
if ($script:deletes -ne 1 -or $null -ne $script:fakeTask) {throw 'Owned removal failed'}
@{native_definition_verified=$true;real_registration=$false;foreign_preserved=$true} | ConvertTo-Json
''')
        self.assertFalse(result["real_registration"])
        self.assertTrue(result["foreign_preserved"])


if __name__ == "__main__":
    unittest.main()
