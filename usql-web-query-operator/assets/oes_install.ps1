param(
    [ValidateSet('Wizard','VerifyPackage','PrepareOnly','InspectUi')][string]$Mode = 'Wizard',
    [string]$InstallRoot,
    [string]$PreviewPath,
    [string]$BundleRoot = $PSScriptRoot
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'installer/core.ps1')
$BundleRoot = Assert-OesLocalRoot $BundleRoot
if ($Mode -eq 'VerifyPackage') {
    $manifest = Test-OesManifest $BundleRoot
    @{status='verified';files=@($manifest.files).Count;registered=$false;power_settings_changed=$false} | ConvertTo-Json
    exit 0
}
if ($Mode -eq 'PrepareOnly') {
    if (-not $InstallRoot) { throw 'PrepareOnly requires an explicit isolated installation directory.' }
    $InstallRoot = Assert-OesLocalRoot $InstallRoot
    $state = Get-OesInstallState $InstallRoot
    # This mode never mutates Task Scheduler, power, credentials or Feishu authorization.
    if ($null -ne (Find-OesTask (Get-OesTaskFolder) $state.task_name)) {
        throw 'PrepareOnly refuses to modify an installation with a registered task.'
    }
    Install-OesFiles $BundleRoot $InstallRoot
    Initialize-OesRuntime $InstallRoot
    @{status='runtime_prepared';directory=$InstallRoot;registered=$false;power_settings_changed=$false} | ConvertTo-Json
    exit 0
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[Windows.Forms.Application]::EnableVisualStyles()
$ui = Read-OesJson (Join-Path $BundleRoot 'installer/ui.zh-CN.json')
$script:OesStage = 'files'
$script:OesBusy = $false
$script:OesPumpUi = { [Windows.Forms.Application]::DoEvents() }
$form = [Windows.Forms.Form]::new()
$form.Text = $ui.title
$form.StartPosition = 'CenterScreen'
$form.Size = [Drawing.Size]::new(840,780)
$form.MinimumSize = $form.Size
$form.Font = [Drawing.Font]::new('Microsoft YaHei UI',10)
$form.AutoScroll = $true

function Add-OesLabel([string]$Text, [int]$Y, [int]$Height = 24) {
    $control = [Windows.Forms.Label]::new()
    $control.Text = $Text; $control.Location = [Drawing.Point]::new(22,$Y)
    $control.Size = [Drawing.Size]::new(770,$Height)
    $form.Controls.Add($control)
    return $control
}
function Add-OesText([string]$Label, [int]$Y, [string]$Value, [bool]$Secret = $false) {
    Add-OesLabel $Label $Y | Out-Null
    $control = [Windows.Forms.TextBox]::new()
    $control.Location = [Drawing.Point]::new(22,($Y+24)); $control.Size = [Drawing.Size]::new(770,28)
    $control.Text = $Value; $control.UseSystemPasswordChar = $Secret
    $form.Controls.Add($control)
    return $control
}
function Add-OesCheck([string]$Text, [int]$Y, [bool]$Checked) {
    $control = [Windows.Forms.CheckBox]::new()
    $control.Text = $Text; $control.Checked = $Checked; $control.Location = [Drawing.Point]::new(22,$Y)
    $control.Size = [Drawing.Size]::new(770,30)
    $form.Controls.Add($control)
    return $control
}
function Add-OesButton([string]$Text, [int]$X, [int]$Y, [int]$Width = 185) {
    $control = [Windows.Forms.Button]::new()
    $control.Text = $Text; $control.Location = [Drawing.Point]::new($X,$Y)
    $control.Size = [Drawing.Size]::new($Width,34)
    $form.Controls.Add($control)
    return $control
}

$default = Read-OesJson (Join-Path $BundleRoot 'installer/profile.default.json')
if (-not $InstallRoot) {
    if (Test-Path -LiteralPath (Join-Path $BundleRoot 'private/install-state.json')) { $InstallRoot = $BundleRoot }
    else { $InstallRoot = Join-Path $env:LOCALAPPDATA 'Gaotu/OesBaseSync' }
}
$existing = Join-Path $InstallRoot 'settings.json'
if (Test-Path -LiteralPath $existing) { $default = Read-OesJson $existing }
Add-OesLabel $ui.intro 12 30 | Out-Null
$rootBox = Add-OesText $ui.root 46 $InstallRoot
$baseBox = Add-OesText $ui.base 106 ('https://gaotuedu.feishu.cn/base/' + $default.base_token + '?table=' + $default.table_id)
$baseBox.ReadOnly=$true
$tableBox=[Windows.Forms.TextBox]::new(); $tableBox.Text=$default.config_table_id
$recordBox=[Windows.Forms.TextBox]::new(); $recordBox.Text=$default.config_record_id
$userBox = Add-OesText $ui.username 166 ''
$passwordBox = Add-OesText $ui.password 226 '' $true
$appBox = Add-OesText $ui.app_id 286 $default.lark_app_id
$secretBox = Add-OesText $ui.app_secret 346 '' $true
Add-OesLabel $ui.app_hint 402 27 | Out-Null
$activateBox = Add-OesCheck $ui.activate 430 $false
$powerBox = Add-OesCheck $ui.power 460 $false
$confirmBox = Add-OesCheck $ui.confirm 490 $false
$installButton = Add-OesButton $ui.install 22 530 375
$checkButton = Add-OesButton $ui.check 409 530
$logsButton = Add-OesButton $ui.logs 606 530
$pauseButton = Add-OesButton $ui.pause 22 572
$removeButton = Add-OesButton $ui.remove 219 572
$restoreButton = Add-OesButton $ui.restore 416 572
$taskButton = Add-OesButton $ui.task_ui 613 572 178
$advancedButton=Add-OesButton $ui.advanced 22 614 375
$status = Add-OesLabel $ui.ready 660 65
$inputControls=@($rootBox,$baseBox,$userBox,$passwordBox,$appBox,$secretBox,$activateBox,$powerBox,$confirmBox,$advancedButton)

function Read-OesAccount([string]$Root) {
    $file = Join-Path $Root 'private/usql_api.env'
    if (-not (Test-Path -LiteralPath $file)) { return '' }
    $text = [IO.File]::ReadAllText($file, [Text.Encoding]::UTF8)
    $match = [regex]::Match($text,'(?m)^BAIJIA_USERNAME="?(.*?)"?\r?$')
    if ($match.Success) { return $match.Groups[1].Value }
    return ''
}
$userBox.Text = Read-OesAccount $InstallRoot

function Set-OesUiStage([string]$Stage) {
    $script:OesStage = $Stage
    $status.Text = $ui.$Stage
    [Windows.Forms.Application]::DoEvents()
}

function Invoke-OesUiAction([scriptblock]$Action) {
    if ($script:OesBusy) { return }
    $script:OesBusy = $true
    foreach ($inputControl in $inputControls) { $inputControl.Enabled=$false }
    foreach ($button in @($installButton,$checkButton,$pauseButton,$removeButton,$restoreButton)) { $button.Enabled=$false }
    try { & $Action }
    catch {
        $stage = $script:OesStage
        $help = $ui.($stage + '_help')
        $status.Text = $ui.error_title + ': ' + $ui.$stage
        # Never expose raw process output, credentials, cookies or exception messages.
        [Windows.Forms.MessageBox]::Show(($ui.error -f $ui.$stage,$help), $ui.error_title,'OK','Error') | Out-Null
    } finally {
        $passwordBox.Clear(); $secretBox.Clear()
        $script:OesBusy=$false
        foreach ($inputControl in $inputControls) { $inputControl.Enabled=$true }
        foreach ($button in @($installButton,$checkButton,$pauseButton,$removeButton,$restoreButton)) { $button.Enabled=$true }
    }
}

function Invoke-OesJob([string]$Root, [string]$Action) {
    $result = Invoke-OesProcess (Join-Path $Root 'runtime/python/python.exe') @(
        (Join-Path $Root 'skills/usql-web-query-operator/scripts/run_oes_base_job.py'),$Action,
        '--settings',(Join-Path $Root 'settings.json')) $Root $null 600
    if ($result.ExitCode -ne 0) { throw 'Job verification or login failed.' }
}

function Initialize-OesBrowser([string]$Root, $Settings) {
    $python = Join-Path $Root 'runtime/python/python.exe'
    $probe = Invoke-OesProcess $python @('-c',
        'from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(channel="msedge"); b.close(); p.stop()') $Root
    if ($probe.ExitCode -eq 0) { $Settings.browser_channel='msedge'; return }
    # Private fallback browser; no system Edge installation or global browser preferences.
    $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $Root 'data/browsers'
    $result = Invoke-OesProcess $python @('-m','playwright','install','chromium') $Root $null 900
    if ($result.ExitCode -ne 0) { throw 'Private Chromium installation failed.' }
    $Settings.browser_channel='chromium'
    $probe = Invoke-OesProcess $python @('-c',
        'from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(channel="chromium"); b.close(); p.stop()') $Root
    if ($probe.ExitCode -ne 0) { throw 'Private browser startup failed.' }
}

function Complete-OesFeishuAuth([string]$Root, $Settings) {
    $cli = Join-Path $Root 'tools/lark-cli.exe'
    $prefix = @('--profile',$Settings.lark_profile)
    if ($secretBox.Text) {
        if ($appBox.Text -notmatch '^cli_[A-Za-z0-9]+$') { throw 'Invalid company Feishu App ID.' }
        $configured = Invoke-OesProcess $cli @('config','init','--name',$Settings.lark_profile,
            '--app-id',$appBox.Text.Trim(),'--app-secret-stdin','--brand','feishu') $Root $secretBox.Text
        if ($configured.ExitCode -ne 0) { throw 'Feishu application setup failed.' }
    } elseif (-not $Settings.lark_app_id -or $Settings.lark_app_id -ne $appBox.Text.Trim()) {
        throw 'First-time or changed application requires App Secret.'
    }
    $Settings.lark_app_id = $appBox.Text.Trim()
    Write-OesJson (Join-Path $Root 'settings.json') $Settings
    $started = Invoke-OesProcess $cli ($prefix + @('auth','login','--domain','base','--no-wait','--json')) $Root
    if ($started.ExitCode -ne 0) { throw 'Could not initiate Feishu user authorization.' }
    $flow = $started.Stdout | ConvertFrom-Json
    if ($flow.ok -eq $false) { throw 'Feishu user authorization was rejected.' }
    if ($flow.data) { $flow=$flow.data }
    $url = $flow.verification_url
    if (-not $url) { $url=$flow.verification_uri_complete }
    if (-not $url) { $url=$flow.verification_uri }
    if (-not $flow.device_code -or -not $url -or -not $url.StartsWith('https://')) { throw 'Unexpected OAuth response.' }
    $qrRelative = 'private/auth-qr-' + [Guid]::NewGuid().ToString('N') + '.png'
    $qrPath = Join-Path $Root $qrRelative
    $dialog = [Windows.Forms.Form]::new()
    $dialog.Text=$ui.auth_title; $dialog.Size=[Drawing.Size]::new(650,510); $dialog.StartPosition='CenterParent'
    $dialog.Font=$form.Font
    try {
        $qr = Invoke-OesProcess $cli @('auth','qrcode',$url,'--output',$qrRelative) $Root
        if ($qr.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $qrPath)) { throw 'Could not create authorization QR.' }
        $hint = [Windows.Forms.Label]::new(); $hint.Text=$ui.auth_wait
        $hint.Location=[Drawing.Point]::new(15,12); $hint.Size=[Drawing.Size]::new(605,45); $dialog.Controls.Add($hint)
        $link = [Windows.Forms.LinkLabel]::new(); $link.Text=$url
        $link.Location=[Drawing.Point]::new(15,60); $link.Size=[Drawing.Size]::new(605,55)
        $link.Add_LinkClicked({ Start-Process -FilePath $url }); $dialog.Controls.Add($link)
        $picture = [Windows.Forms.PictureBox]::new(); $picture.Location=[Drawing.Point]::new(180,120)
        $picture.Size=[Drawing.Size]::new(256,256); $picture.SizeMode='Zoom'
        $original = [Drawing.Image]::FromFile($qrPath)
        try { $picture.Image=$original.Clone() } finally { $original.Dispose() }
        $dialog.Controls.Add($picture)
        $continue = [Windows.Forms.Button]::new(); $continue.Text=$ui.auth_continue
        $continue.Location=[Drawing.Point]::new(30,395); $continue.Size=[Drawing.Size]::new(340,38)
        $continue.DialogResult='OK'; $dialog.Controls.Add($continue)
        $cancel = [Windows.Forms.Button]::new(); $cancel.Text=$ui.auth_cancel
        $cancel.Location=[Drawing.Point]::new(390,395); $cancel.Size=[Drawing.Size]::new(200,38)
        $cancel.DialogResult='Cancel'; $dialog.Controls.Add($cancel)
        if ($dialog.ShowDialog($form) -ne 'OK') { throw 'User canceled authorization.' }
        $finished = Invoke-OesProcess $cli ($prefix + @('auth','login','--device-code',$flow.device_code)) $Root
        if ($finished.ExitCode -ne 0) { throw 'Feishu user authorization did not complete.' }
    } finally {
        if ($picture -and $picture.Image) { $picture.Image.Dispose() }
        $dialog.Dispose()
        if (Test-Path -LiteralPath $qrPath) { Remove-Item -LiteralPath $qrPath -Force }
        $flow=$null; $url=$null
    }
}

function Invoke-OesElevatedPower([string]$Root, $State, [string]$Action) {
    $resultPath = Join-Path $Root 'private/power-result.json'
    if (Test-Path -LiteralPath $resultPath) { Remove-Item -LiteralPath $resultPath -Force }
    $scriptPath = Join-Path $Root 'power.ps1'
    $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $scriptPath + '" -Mode ' + $Action +
                 ' -Root "' + $Root + '" -ExpectedSid ' + $State.owner_sid
    $process = Start-Process -FilePath "$env:SystemRoot/System32/WindowsPowerShell/v1.0/powershell.exe" -Verb RunAs -WindowStyle Hidden -ArgumentList $arguments -PassThru
    try {
        while (-not $process.HasExited) { [Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 100 }
        $process.WaitForExit()
        $result = Read-OesJson $resultPath
        $expected = 'applied'; if ($Action -eq 'Restore') { $expected='restored' }
        if ($process.ExitCode -ne 0 -or $result.status -ne $expected -or $result.verified -ne $true -or
            $result.installation_id -ne $State.installation_id) { throw 'Power operation did not pass readback.' }
    } finally { $process.Dispose() }
}

function New-OesManagementShortcut([string]$Root) {
    $desktop=[Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)
    $shell=New-Object -ComObject WScript.Shell
    $name=$ui.shortcut + '-' + (Get-OesHash $Root).Substring(0,8) + '.lnk'
    $shortcut=$shell.CreateShortcut((Join-Path $desktop $name))
    $shortcut.TargetPath="$env:SystemRoot/System32/WindowsPowerShell/v1.0/powershell.exe"
    $shortcut.Arguments='-NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + (Join-Path $Root 'install.ps1') + '"'
    $shortcut.WorkingDirectory=$Root
    $shortcut.WindowStyle=7
    $shortcut.Description=$ui.title
    $shortcut.Save()
}

$installButton.Add_Click({ Invoke-OesUiAction {
    Set-OesUiStage 'files'
    if (-not $confirmBox.Checked -or -not $userBox.Text.Trim() -or
        $tableBox.Text -notmatch '^tbl[A-Za-z0-9]+$' -or $recordBox.Text -notmatch '^rec[A-Za-z0-9]+$') {
        [Windows.Forms.MessageBox]::Show($ui.confirmation_required,$ui.title) | Out-Null
        return
    }
    $options=@{root=$rootBox.Text; base_url=$baseBox.Text; config_table_id=$tableBox.Text.Trim();
        config_record_id=$recordBox.Text.Trim();username=$userBox.Text.Trim();password=$passwordBox.Text;
        confirm_replace=$confirmBox.Checked;activate=$activateBox.Checked;power=$powerBox.Checked}
    try {
        $result=Invoke-OesDeployment $BundleRoot $options {param($stage) Set-OesUiStage $stage} `
            {param($root,$settings) Initialize-OesBrowser $root $settings} `
            {param($root,$settings) Complete-OesFeishuAuth $root $settings} `
            {param($root,$action) Invoke-OesJob $root $action} `
            {param($root,$state,$action) Invoke-OesElevatedPower $root $state $action}
        # A desktop-policy restriction does not undo a fully verified deployment.
        try { New-OesManagementShortcut $result.root } catch {}
        $status.Text=$ui.complete + "`n" + $result.root + ' | ' + $result.task_name + ' | ' + $result.status + ' | ' + $result.row_count
    } finally { $options.password=$null }
} })
$checkButton.Add_Click({ Invoke-OesUiAction {
    Set-OesUiStage 'mail'
    $root = Assert-OesLocalRoot $rootBox.Text
    Get-OesInstallState $root | Out-Null
    Invoke-OesJob $root 'health'
    $status.Text=$ui.check_ok
} })
$pauseButton.Add_Click({ Invoke-OesUiAction {
    Set-OesUiStage 'scheduler'
    $root=Assert-OesLocalRoot $rootBox.Text; $state=Get-OesInstallState $root
    Disable-OesTask $state; Save-OesInstallState $root $state 'disabled' 'paused'
    $status.Text=$ui.task_paused
} })
$removeButton.Add_Click({ Invoke-OesUiAction {
    Set-OesUiStage 'scheduler'
    if ([Windows.Forms.MessageBox]::Show($ui.remove_confirm,$ui.title,'YesNo','Question') -ne 'Yes') { return }
    $root=Assert-OesLocalRoot $rootBox.Text; $state=Get-OesInstallState $root
    Remove-OesTask $state; Save-OesInstallState $root $state 'removed' 'removed'
    $status.Text=$ui.task_removed
} })
$restoreButton.Add_Click({ Invoke-OesUiAction {
    Set-OesUiStage 'scheduler'
    $root=Assert-OesLocalRoot $rootBox.Text; $state=Get-OesInstallState $root
    Suspend-OesTask $state; Invoke-OesElevatedPower $root $state 'Restore'
    Save-OesInstallState $root $state 'disabled' 'power_restored'; $status.Text=$ui.power_ok
} })
$logsButton.Add_Click({
    $root=Assert-OesLocalRoot $rootBox.Text
    $path=Join-Path $root 'data'
    if (Test-Path -LiteralPath $path) { Start-Process -FilePath 'explorer.exe' -ArgumentList ('"' + $path + '"') }
})
$taskButton.Add_Click({ Start-Process -FilePath "$env:SystemRoot/System32/mmc.exe" -ArgumentList 'taskschd.msc' })
$advancedButton.Add_Click({
    $dialog=[Windows.Forms.Form]::new(); $dialog.Text=$ui.advanced
    $dialog.Size=[Drawing.Size]::new(800,355); $dialog.StartPosition='CenterParent'; $dialog.Font=$form.Font
    $boxes=@()
    for ($i=0; $i -lt 3; $i++) {
        $label=[Windows.Forms.Label]::new(); $label.Text=@($ui.base,$ui.config_table,$ui.config_record)[$i]
        $label.Location=[Drawing.Point]::new(15,(15+75*$i)); $label.Size=[Drawing.Size]::new(745,25)
        $dialog.Controls.Add($label)
        $box=[Windows.Forms.TextBox]::new(); $box.Text=@($baseBox.Text,$tableBox.Text,$recordBox.Text)[$i]
        $box.Location=[Drawing.Point]::new(15,(40+75*$i)); $box.Size=[Drawing.Size]::new(745,28)
        $dialog.Controls.Add($box); $boxes+=,$box
    }
    $ok=[Windows.Forms.Button]::new(); $ok.Text=$ui.save; $ok.DialogResult='OK'
    $ok.Location=[Drawing.Point]::new(15,260); $ok.Size=[Drawing.Size]::new(200,35); $dialog.Controls.Add($ok)
    try {
        if ($dialog.ShowDialog($form) -eq 'OK') { $baseBox.Text=$boxes[0].Text; $tableBox.Text=$boxes[1].Text; $recordBox.Text=$boxes[2].Text }
    } finally { $dialog.Dispose() }
})
$form.Add_FormClosing({ param($sender,$event)
    if ($script:OesBusy) { $event.Cancel=$true; $status.Text=$ui.close_busy }
})
if ($Mode -eq 'InspectUi') {
    if ($PreviewPath) {
        # Create child handles without displaying a visible test window.
        $form.ShowInTaskbar=$false; $form.Opacity=0; $form.FormBorderStyle='None'
        $form.Show(); [Windows.Forms.Application]::DoEvents(); $form.PerformLayout()
        $bitmap=[Drawing.Bitmap]::new($form.Width,$form.Height)
        try { $form.DrawToBitmap($bitmap,[Drawing.Rectangle]::new(0,0,$form.Width,$form.Height)); $bitmap.Save($PreviewPath) }
        finally { $bitmap.Dispose(); $form.Hide() }
    }
    @{status='ui_constructed';title=$form.Text;controls=$form.Controls.Count;password_masked=$passwordBox.UseSystemPasswordChar;
      app_secret_masked=$secretBox.UseSystemPasswordChar;replacement_confirmed=$confirmBox.Checked;
      registered=$false;power_settings_changed=$false} | ConvertTo-Json
    $form.Dispose()
    exit 0
}
try { [Windows.Forms.Application]::Run($form) } finally { $form.Dispose() }
