# Remove ImgBatch parent menu + CommandStore submenu entries (HKCU).

$ErrorActionPreference = "Stop"

$actions = @("compress", "convert", "rename", "watermark", "trim", "normalize", "inspect")
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

$hkcu = [Microsoft.Win32.Registry]::CurrentUser
foreach ($cr in $classRoots) {
    foreach ($name in $flat) {
        $rel = "Software\Classes\$cr\shell\$name"
        try { $hkcu.DeleteSubKeyTree($rel, $false); Write-Host "Removed HKCU:\$rel" } catch {}
    }
}
foreach ($a in $actions) {
    foreach ($prefix in @("ImgBatch.", "ImgBatch.dir.")) {
        $rel = "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\$prefix$a"
        try { $hkcu.DeleteSubKeyTree($rel, $false); Write-Host "Removed HKCU:\$rel" } catch {}
    }
}

Write-Host "Done."
