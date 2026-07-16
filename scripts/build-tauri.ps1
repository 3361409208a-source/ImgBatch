$ErrorActionPreference = "Stop"
.\scripts\build-sidecar.ps1
.\scripts\build-frontend.ps1
Push-Location src-tauri
cargo tauri build
Pop-Location
Write-Host "Installer in src-tauri/target/release/bundle/"
