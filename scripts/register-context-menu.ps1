# Register ImgBatch parent menu + action submenus (HKCU CommandStore).
# Usage:
#   .\scripts\register-context-menu.ps1
#   .\scripts\register-context-menu.ps1 -ExePath "C:\path\to\imgbatch.exe"

param(
    [string]$ExePath = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not $ExePath) {
    $candidates = @(
        (Join-Path $root "src-tauri\target\release\imgbatch.exe"),
        (Join-Path $root "src-tauri\target\release\ImgBatch.exe"),
        (Join-Path $root "src-tauri\target\debug\imgbatch.exe"),
        (Join-Path $root "src-tauri\target\debug\ImgBatch.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) { $ExePath = (Resolve-Path -LiteralPath $c).Path; break }
    }
}

if (-not $ExePath -or -not (Test-Path -LiteralPath $ExePath)) {
    Write-Error "imgbatch.exe not found. Build first or pass -ExePath."
}

. (Join-Path $PSScriptRoot "context-menu-common.ps1")
Register-ImgBatchContextMenu -Hive ([Microsoft.Win32.Registry]::CurrentUser) -ExePath $ExePath
Write-Host "Registered ImgBatch menus with submenus -> $ExePath"
