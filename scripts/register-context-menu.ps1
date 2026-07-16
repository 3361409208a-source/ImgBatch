# Register one parent "ImgBatch" menu + submenu via Explorer CommandStore (HKCU).
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

$actions = @(
    @{ Id = "compress"; Label = [string]([char]0x538B) + [char]0x7F29 },
    @{ Id = "convert"; Label = [string]([char]0x683C) + [char]0x5F0F + [char]0x8F6C + [char]0x6362 },
    @{ Id = "rename"; Label = [string]([char]0x91CD) + [char]0x547D + [char]0x540D },
    @{ Id = "watermark"; Label = [string]([char]0x6C34) + [char]0x5370 },
    @{ Id = "trim"; Label = [string]([char]0x88C1) + [char]0x8FB9 },
    @{ Id = "normalize"; Label = [string]([char]0x89C4) + [char]0x8303 + [char]0x5316 },
    @{ Id = "inspect"; Label = [string]([char]0x68C0) + [char]0x67E5 }
)

$fileSub = ($actions | ForEach-Object { "ImgBatch.$($_.Id)" }) -join ";"
$dirSub = ($actions | ForEach-Object { "ImgBatch.dir.$($_.Id)" }) -join ";"

function Remove-Key([Microsoft.Win32.RegistryKey]$Hive, [string]$Rel) {
    try { $Hive.DeleteSubKeyTree($Rel, $false) } catch {}
}

function Clear-Old([Microsoft.Win32.RegistryKey]$Hive) {
    $flat = @(
        "ImgBatch", "ImgBatchSep",
        "ImgBatchCompress", "ImgBatchConvert", "ImgBatchRename",
        "ImgBatchWatermark", "ImgBatchTrim", "ImgBatchNormalize", "ImgBatchInspect"
    )
    $classRoots = @(
        "*", "Directory", "Directory\Background",
        ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".ico",
        "SystemFileAssociations\image"
    )
    foreach ($cr in $classRoots) {
        foreach ($name in $flat) {
            Remove-Key $Hive "Software\Classes\$cr\shell\$name"
        }
    }
    foreach ($a in $actions) {
        Remove-Key $Hive "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.$($a.Id)"
        Remove-Key $Hive "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.$($a.Id)"
    }
}

function Write-Store([Microsoft.Win32.RegistryKey]$Hive, [string]$StoreId, [string]$Label, [string]$Action, [string]$ArgToken) {
    $key = $Hive.CreateSubKey("Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\$StoreId")
    $key.SetValue("MUIVerb", $Label)
    $key.SetValue("Icon", "$ExePath,0")
    $key.SetValue("MultiSelectModel", "Player")
    $cmd = $key.CreateSubKey("command")
    $cmd.SetValue("", "`"$ExePath`" --quick $Action $ArgToken")
    $cmd.Close()
    $key.Close()
}

function Write-Parent([Microsoft.Win32.RegistryKey]$Hive, [string]$ClassRoot, [string]$SubCommands) {
    $key = $Hive.CreateSubKey("Software\Classes\$ClassRoot\shell\ImgBatch")
    $key.SetValue("MUIVerb", "ImgBatch")
    $key.SetValue("Icon", "$ExePath,0")
    $key.SetValue("SubCommands", $SubCommands)
    $key.Close()
}

$hkcu = [Microsoft.Win32.Registry]::CurrentUser
Clear-Old $hkcu

foreach ($a in $actions) {
    Write-Store $hkcu "ImgBatch.$($a.Id)" $a.Label $a.Id '"%1"'
    Write-Store $hkcu "ImgBatch.dir.$($a.Id)" $a.Label $a.Id '"%V"'
}

Write-Parent $hkcu "*" $fileSub
Write-Parent $hkcu "Directory" $dirSub
Write-Parent $hkcu "Directory\Background" $dirSub

Write-Host "Registered ImgBatch parent menu + submenu -> $ExePath"
Write-Host "SubCommands (files): $fileSub"
