# Requires Administrator. Sync HKLM to parent+submenu (CommandStore) layout.

#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

$exeCandidates = @(
    "${env:ProgramFiles}\ImgBatch\imgbatch.exe",
    "${env:ProgramFiles(x86)}\ImgBatch\imgbatch.exe",
    "$PSScriptRoot\..\src-tauri\target\release\imgbatch.exe"
)
$ExePath = $exeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $ExePath) { Write-Error "imgbatch.exe not found" }
$ExePath = (Resolve-Path -LiteralPath $ExePath).Path

. (Join-Path $PSScriptRoot "context-menu-common.ps1")
Register-ImgBatchContextMenu -Hive ([Microsoft.Win32.Registry]::LocalMachine) -ExePath $ExePath
Write-Host "HKLM parent+submenu fixed -> $ExePath"
