# Load credentials from .env file and run usql login.
# Usage: powershell -ExecutionPolicy Bypass -File _login_helper.ps1 [--manual] [--headed]

$envFile = "E:\1900_work\GAOTU\19002_市场顾问部看板维护表格\usql_api.env"
$script  = "c:\Users\Ludim\.codex\skills\usql-web-query-operator\scripts\usql_web_query.py"
$python  = "D:\anaconda3\python.exe"

Get-Content -Encoding UTF8 $envFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and $line -notmatch '^\s*#') {
        if ($line -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim() -replace '^["'']|["'']$', ''
            [Environment]::SetEnvironmentVariable($key, $val, 'Process')
        }
    }
}

$argsList = @($script, "login")
if ($args.Count -gt 0) {
    $argsList += $args
}

Write-Host "Running: $python $($argsList -join ' ')" -ForegroundColor Cyan
& $python @argsList
