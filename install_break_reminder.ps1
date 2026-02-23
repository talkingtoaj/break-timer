# Break reminder - PowerShell installer
# Downloads the latest Break.reminder.exe from GitHub Releases and adds to Windows startup.
# Requires: internet connection. Run in PowerShell (or: powershell -ExecutionPolicy Bypass -File install_break_reminder.ps1)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$repo = 'https://github.com/talkingtoaj/break-timer'
$installDir = Join-Path $env:LOCALAPPDATA 'Break reminder'
# Asset on GitHub Releases is named Break.reminder.exe (dot, not space)
$exeName = 'Break.reminder.exe'
$exePath = Join-Path $installDir $exeName
$downloadUrl = "$repo/releases/latest/download/$exeName"

Write-Host 'Break reminder - Installer' -ForegroundColor Cyan
Write-Host ''
Write-Host "This will download the latest release from GitHub and install to:"
Write-Host "  $installDir"
Write-Host ''

if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

Write-Host "Downloading $exeName..."
$downloaded = $false
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $exePath -UseBasicParsing
    $downloaded = $true
} catch {
    Write-Host "Invoke-WebRequest failed: $_" -ForegroundColor Yellow
    Write-Host 'Trying curl.exe fallback...'
}
if (-not $downloaded) {
    try {
        & curl.exe -fL -o $exePath $downloadUrl
        if (($LASTEXITCODE -eq 0) -and (Test-Path $exePath)) { $downloaded = $true }
    } catch {
        Write-Host "curl failed: $_" -ForegroundColor Red
    }
}
if (-not $downloaded) {
    Write-Host "Download failed. Please download the exe from: $repo/releases/latest" -ForegroundColor Red
    exit 1
}
Write-Host 'Download complete.' -ForegroundColor Green

Write-Host ''
Write-Host 'Adding to Windows startup...'
& $exePath --install

Write-Host ''
Write-Host 'Done. Break reminder is installed at:' -ForegroundColor Green
Write-Host "  $exePath"
Write-Host 'It will start automatically when you log in.'
Write-Host ''
explorer $installDir
