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
    foreach ($a in $leafActions) {
        Remove-Key $Hive "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.$($a.Id)"
        Remove-Key $Hive "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.$($a.Id)"
    }
    Remove-Key $Hive "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert"
    Remove-Key $Hive "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert"
    foreach ($f in $convertFormats) {
        Remove-Key $Hive "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.convert.$($f.Id)"
        Remove-Key $Hive "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ImgBatch.dir.convert.$($f.Id)"
    }
}

function Write-StoreVerb(
    [Microsoft.Win32.RegistryKey]$Hive,
    [string]$StoreId,
    [string]$Label,
    [string]$CommandLine
) {
    $key = $Hive.CreateSubKey("Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\$StoreId")
    $key.SetValue("MUIVerb", $Label)
    $key.SetValue("Icon", "$ExePath,0")
    $key.SetValue("MultiSelectModel", "Player")
    $cmd = $key.CreateSubKey("command")
    $cmd.SetValue("", $CommandLine)
    $cmd.Close()
    $key.Close()
}

function Write-StoreParent(
    [Microsoft.Win32.RegistryKey]$Hive,
    [string]$StoreId,
    [string]$Label,
    [string]$SubCommands
) {
    $key = $Hive.CreateSubKey("Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\$StoreId")
    $key.SetValue("MUIVerb", $Label)
    $key.SetValue("Icon", "$ExePath,0")
    $key.SetValue("SubCommands", $SubCommands)
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

foreach ($a in $leafActions) {
    $cmd = "`"$ExePath`" --quick $($a.Id) `"%1`""
    Write-StoreVerb $hkcu "ImgBatch.$($a.Id)" $a.Label $cmd
    $dirCmd = "`"$ExePath`" --quick $($a.Id) `"%V`""
    Write-StoreVerb $hkcu "ImgBatch.dir.$($a.Id)" $a.Label $dirCmd
}

Write-StoreParent $hkcu "ImgBatch.convert" $convertLabel $fileConvertSub
Write-StoreParent $hkcu "ImgBatch.dir.convert" $convertLabel $dirConvertSub

foreach ($f in $convertFormats) {
    $label = "$convertToLabel $($f.Label)"
    $fileCmd = "`"$ExePath`" --quick convert --format $($f.Ext) `"%1`""
    $dirCmd = "`"$ExePath`" --quick convert --format $($f.Ext) `"%V`""
    Write-StoreVerb $hkcu "ImgBatch.convert.$($f.Id)" $label $fileCmd
    Write-StoreVerb $hkcu "ImgBatch.dir.convert.$($f.Id)" $label $dirCmd
}

Write-Parent $hkcu "*" $fileSub
Write-Parent $hkcu "Directory" $dirSub
Write-Parent $hkcu "Directory\Background" $dirSub

Write-Host "Registered ImgBatch parent menu + submenu -> $ExePath"
Write-Host "SubCommands (files): $fileSub"
