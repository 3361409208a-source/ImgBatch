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

$leafActions = @(
    @{ Id = "compress"; Label = [string]([char]0x538B) + [char]0x7F29 },
    @{ Id = "rename"; Label = [string]([char]0x91CD) + [char]0x547D + [char]0x540D },
    @{ Id = "watermark"; Label = [string]([char]0x6C34) + [char]0x5370 },
    @{ Id = "trim"; Label = [string]([char]0x88C1) + [char]0x8FB9 },
    @{ Id = "normalize"; Label = [string]([char]0x89C4) + [char]0x8303 + [char]0x5316 },
    @{ Id = "inspect"; Label = [string]([char]0x68C0) + [char]0x67E5 }
)

$convertLabel = [string]([char]0x683C) + [char]0x5F0F + [char]0x8F6C + [char]0x6362
$convertToLabel = [string]([char]0x8F6C) + [char]0x4E3A

$convertFormats = @(
    @{ Id = "png"; Ext = ".png"; Label = "PNG" },
    @{ Id = "jpg"; Ext = ".jpg"; Label = "JPG" },
    @{ Id = "webp"; Ext = ".webp"; Label = "WEBP" },
    @{ Id = "bmp"; Ext = ".bmp"; Label = "BMP" },
    @{ Id = "tiff"; Ext = ".tiff"; Label = "TIFF" },
    @{ Id = "gif"; Ext = ".gif"; Label = "GIF" },
    @{ Id = "ico"; Ext = ".ico"; Label = "ICO" }
)

$fileConvertSub = ($convertFormats | ForEach-Object { "ImgBatch.convert.$($_.Id)" }) -join ";"
$dirConvertSub = ($convertFormats | ForEach-Object { "ImgBatch.dir.convert.$($_.Id)" }) -join ";"
$fileSub = "ImgBatch.compress;ImgBatch.convert;ImgBatch.rename;ImgBatch.watermark;ImgBatch.trim;ImgBatch.normalize;ImgBatch.inspect"
$dirSub = "ImgBatch.dir.compress;ImgBatch.dir.convert;ImgBatch.dir.rename;ImgBatch.dir.watermark;ImgBatch.dir.trim;ImgBatch.dir.normalize;ImgBatch.dir.inspect"

function Remove-Key([string]$Rel) {
    try { [Microsoft.Win32.Registry]::LocalMachine.DeleteSubKeyTree($Rel, $false) } catch {}
}

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
    foreach ($name in $flat) { Remove-Key "Software\Classes\$cr\shell\$name" }
}
foreach ($a in $leafActions) {
    Remove-Key "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.$($a.Id)"
    Remove-Key "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.$($a.Id)"
}
Remove-Key "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert"
Remove-Key "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert"
foreach ($f in $convertFormats) {
    Remove-Key "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.$($f.Id)"
    Remove-Key "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.$($f.Id)"
}

function Write-StoreVerb([string]$StoreId, [string]$Label, [string]$CommandLine) {
    $key = [Microsoft.Win32.Registry]::LocalMachine.CreateSubKey("Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\$StoreId")
    $key.SetValue("MUIVerb", $Label)
    $key.SetValue("Icon", "$ExePath,0")
    $key.SetValue("MultiSelectModel", "Player")
    $cmd = $key.CreateSubKey("command")
    $cmd.SetValue("", $CommandLine)
    $cmd.Close()
    $key.Close()
}

function Write-StoreParent([string]$StoreId, [string]$Label, [string]$SubCommands) {
    $key = [Microsoft.Win32.Registry]::LocalMachine.CreateSubKey("Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\$StoreId")
    $key.SetValue("MUIVerb", $Label)
    $key.SetValue("Icon", "$ExePath,0")
    $key.SetValue("SubCommands", $SubCommands)
    $key.Close()
}

function Write-Parent([string]$ClassRoot, [string]$SubCommands) {
    $key = [Microsoft.Win32.Registry]::LocalMachine.CreateSubKey("Software\Classes\$ClassRoot\shell\ImgBatch")
    $key.SetValue("MUIVerb", "ImgBatch")
    $key.SetValue("Icon", "$ExePath,0")
    $key.SetValue("SubCommands", $SubCommands)
    $key.Close()
}

foreach ($a in $leafActions) {
    Write-StoreVerb "ImgBatch.$($a.Id)" $a.Label "`"$ExePath`" --quick $($a.Id) `"%1`""
    Write-StoreVerb "ImgBatch.dir.$($a.Id)" $a.Label "`"$ExePath`" --quick $($a.Id) `"%V`""
}

Write-StoreParent "ImgBatch.convert" $convertLabel $fileConvertSub
Write-StoreParent "ImgBatch.dir.convert" $convertLabel $dirConvertSub

foreach ($f in $convertFormats) {
    $label = "$convertToLabel $($f.Label)"
    Write-StoreVerb "ImgBatch.convert.$($f.Id)" $label "`"$ExePath`" --quick convert --format $($f.Ext) `"%1`""
    Write-StoreVerb "ImgBatch.dir.convert.$($f.Id)" $label "`"$ExePath`" --quick convert --format $($f.Ext) `"%V`""
}

Write-Parent "*" $fileSub
Write-Parent "Directory" $dirSub
Write-Parent "Directory\Background" $dirSub

Write-Host "HKLM parent+submenu fixed -> $ExePath"
