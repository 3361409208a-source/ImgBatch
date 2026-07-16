# Remove ImgBatch parent menu + CommandStore submenu entries (HKCU).

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\context-menu-common.ps1"

Clear-ImgBatchContextMenu -Hive ([Microsoft.Win32.Registry]::CurrentUser)
Write-Host "Removed ImgBatch context menus from HKCU."
