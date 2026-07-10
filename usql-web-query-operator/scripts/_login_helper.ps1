# Run USQL login with the shared environment-file configuration.
# Usage: powershell -ExecutionPolicy Bypass -File _login_helper.ps1 [--manual] [--headed]

$script  = "c:\Users\Ludim\.codex\skills\usql-web-query-operator\scripts\usql_web_query.py"
$python  = "D:\anaconda3\python.exe"

$argsList = @($script, "login")
if (-not [string]::IsNullOrWhiteSpace($env:USQL_ENV_FILE)) {
    $argsList += @("--env-file", $env:USQL_ENV_FILE)
}
if ($args.Count -gt 0) {
    $argsList += $args
}

Write-Host "Running: $python $($argsList -join ' ')" -ForegroundColor Cyan
& $python @argsList
