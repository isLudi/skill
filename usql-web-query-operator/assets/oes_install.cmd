@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0install.ps1"
if errorlevel 1 (
  echo Installer could not start. Contact IT if PowerShell is blocked by company policy.
  pause
)
