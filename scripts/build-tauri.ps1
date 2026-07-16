$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
.\scripts\build-sidecar.ps1
.\scripts\build-frontend.ps1
npm run tauri build
Write-Host "Installer in src-tauri/target/release/bundle/"
