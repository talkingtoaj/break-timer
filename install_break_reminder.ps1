# Break reminder - PowerShell installer
# Downloads the latest Break reminder.exe from GitHub Releases and adds to Windows startup.
# Requires: internet connection. Run in PowerShell (or: powershell -ExecutionPolicy Bypass -File install_break_reminder.ps1)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$repo = 'https://github.com/talkingtoaj/break-timer'
$installDir = Join-Path $env:LOCALAPPDATA 'Break reminder'
$exePath = Join-Path $installDir 'Break reminder.exe'
$downloadUrl = "$repo/releases/latest/download/Break%20reminder.exe"

Write-Host 'Break reminder - Installer' -ForegroundColor Cyan
Write-Host ''
Write-Host "This will download the latest release from GitHub and install to:"
Write-Host "  $installDir"
Write-Host ''

if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

Write-Host 'Downloading Break reminder.exe...'
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $exePath -UseBasicParsing
    Write-Host 'Download complete.' -ForegroundColor Green
} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    Write-Host "Please download the exe from: $repo/releases/latest"
    exit 1
}

Write-Host ''
Write-Host 'Adding to Windows startup...'
& $exePath --install

Write-Host ''
Write-Host 'Done. Break reminder is installed at:' -ForegroundColor Green
Write-Host "  $exePath"
Write-Host 'It will start automatically when you log in.'
Write-Host ''
explorer $installDir
