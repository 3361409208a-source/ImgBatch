# Remove ImgBatch context menus registered for the current user (HKCU).

$ErrorActionPreference = "Stop"

$rels = @(
    "Software\Classes\*\shell\ImgBatch",
    "Software\Classes\Directory\shell\ImgBatch",
    "Software\Classes\Directory\Background\shell\ImgBatch",
    "Software\Classes\.png\shell\ImgBatch",
    "Software\Classes\.jpg\shell\ImgBatch",
    "Software\Classes\.jpeg\shell\ImgBatch",
    "Software\Classes\.webp\shell\ImgBatch",
    "Software\Classes\.gif\shell\ImgBatch",
    "Software\Classes\.bmp\shell\ImgBatch",
    "Software\Classes\.tif\shell\ImgBatch",
    "Software\Classes\.tiff\shell\ImgBatch",
    "Software\Classes\.ico\shell\ImgBatch",
    "Software\Classes\SystemFileAssociations\image\shell\ImgBatch"
)

foreach ($rel in $rels) {
    try {
        [Microsoft.Win32.Registry]::CurrentUser.DeleteSubKeyTree($rel, $false)
        Write-Host "Removed HKCU:\$rel"
    } catch {
        # key missing — ignore
    }
}

Write-Host "Done."
