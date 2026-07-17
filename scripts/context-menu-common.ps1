# Shared Explorer context menu definitions for ImgBatch.
# Dot-source from register-context-menu.ps1 (HKCU) or fix-hklm-context-menu.ps1 (HKLM).

$script:ConvertFormats = @(
    @{ Id = "png"; Ext = ".png"; Label = "PNG" },
    @{ Id = "jpg"; Ext = ".jpg"; Label = "JPG" },
    @{ Id = "webp"; Ext = ".webp"; Label = "WEBP" },
    @{ Id = "avif"; Ext = ".avif"; Label = "AVIF" },
    @{ Id = "bmp"; Ext = ".bmp"; Label = "BMP" },
    @{ Id = "tiff"; Ext = ".tiff"; Label = "TIFF" },
    @{ Id = "gif"; Ext = ".gif"; Label = "GIF" },
    @{ Id = "ico"; Ext = ".ico"; Label = "ICO" }
)

$script:ActionMenus = @(
    @{
        Id = "compress"
        Label = [string]([char]0x538B) + [char]0x7F29
        Items = @(
            @{ Id = "high"; Label = [string]([char]0x9AD8) + [char]0x8D28 + [char]0x91CF + " (90)"; Args = "compress --quality 90 --auto-run" },
            @{ Id = "standard"; Label = [string]([char]0x6807) + [char]0x51C6 + " (75)"; Args = "compress --quality 75 --auto-run" },
            @{ Id = "max"; Label = [string]([char]0x6781) + [char]0x9650 + [char]0x538B + [char]0x7F29 + " (50)"; Args = "compress --quality 50 --auto-run" },
            @{ Id = "thumb"; Label = [string]([char]0x7F29) + [char]0x7565 + [char]0x56FE + " 50%"; Args = "compress --quality 50 --resize 50 --auto-run" }
        )
    },
    @{
        Id = "rename"
        Label = [string]([char]0x91CD) + [char]0x547D + [char]0x540D
        Items = @(
            @{ Id = "prefix"; Label = [string]([char]0x5E8F) + [char]0x53F7 + [char]0x524D + [char]0x7F00; Args = "rename --rename-mode prefix --auto-run" },
            @{ Id = "lower"; Label = [string]([char]0x8F6C) + [char]0x5C0F + [char]0x5199; Args = "rename --rename-mode lowercase --auto-run" },
            @{ Id = "upper"; Label = [string]([char]0x8F6C) + [char]0x5927 + [char]0x5199; Args = "rename --rename-mode uppercase --auto-run" },
            @{ Id = "suffix"; Label = [string]([char]0x6DFB) + [char]0x52A0 + [char]0x540E + [char]0x7F00 + "_bak"; Args = "rename --rename-mode suffix --auto-run" }
        )
    },
    @{
        Id = "watermark"
        Label = [string]([char]0x6C34) + [char]0x5370
        Items = @(
            @{ Id = "br"; Label = [string]([char]0x53F3) + [char]0x4E0B + [char]0x6C34 + [char]0x5370; Args = 'watermark --wm-position bottom-right --wm-text ImgBatch --auto-run' },
            @{ Id = "center"; Label = [string]([char]0x5C45) + [char]0x4E2D + [char]0x6C34 + [char]0x5370; Args = "watermark --wm-position center --wm-text ImgBatch --auto-run" },
            @{ Id = "tl"; Label = [string]([char]0x5DE6) + [char]0x4E0A + [char]0x6C34 + [char]0x5370; Args = "watermark --wm-position top-left --wm-text ImgBatch --auto-run" },
            @{ Id = "copy"; Label = [string]([char]0x7248) + [char]0x6743 + " ©"; Args = 'watermark --wm-position bottom-right --wm-text "© ImgBatch" --auto-run' }
        )
    },
    @{
        Id = "trim"
        Label = [string]([char]0x88C1) + [char]0x8FB9
        Items = @(
            @{ Id = "p0"; Label = [string]([char]0x65E0) + [char]0x8FB9 + [char]0x8DDD; Args = "trim --padding 0 --auto-run" },
            @{ Id = "p4"; Label = [string]([char]0x6807) + [char]0x51C6 + " 4px"; Args = "trim --padding 4 --auto-run" },
            @{ Id = "p8"; Label = [string]([char]0x5BBD) + [char]0x8FB9 + [char]0x8DDD + " 8px"; Args = "trim --padding 8 --auto-run" }
        )
    },
    @{
        Id = "normalize"
        Label = [string]([char]0x89C4) + [char]0x8303 + [char]0x5316
        Items = @(
            @{ Id = "h280"; Label = [string]([char]0x9AD8) + [char]0x5EA6 + " 280"; Args = "normalize --target-height 280 --auto-run" },
            @{ Id = "h512"; Label = [string]([char]0x9AD8) + [char]0x5EA6 + " 512"; Args = "normalize --target-height 512 --auto-run" },
            @{ Id = "h1024"; Label = [string]([char]0x9AD8) + [char]0x5EA6 + " 1024"; Args = "normalize --target-height 1024 --auto-run" }
        )
    },
    @{
        Id = "inspect"
        Label = [string]([char]0x68C0) + [char]0x67E5
        Items = @(
            @{ Id = "quick"; Label = ([string]([char]0x5FEB) + [char]0x901F + [char]0x68C0 + [char]0x67E5 + " PNG"); Args = "inspect --auto-run" },
            @{ Id = "open"; Label = ([string]([char]0x6253) + [char]0x5F00 + [char]0x68C0 + [char]0x67E5 + [char]0x9762 + [char]0x677F); Args = "inspect" }
        )
    },
    @{
        Id = "gif"
        Label = "GIF " + [string]([char]0x52A8) + [char]0x56FE
        Items = @(
            @{ Id = "optimize"; Label = ([string]([char]0x4F18) + [char]0x5316 + [char]0x4F53 + [char]0x79EF); Args = "gif --gif-mode optimize --auto-run" },
            @{ Id = "resize50"; Label = [string]([char]0x7F29) + [char]0x5C0F + " 50%"; Args = "gif --gif-mode resize --resize 50 --auto-run" },
            @{ Id = "resize75"; Label = [string]([char]0x7F29) + [char]0x5C0F + " 75%"; Args = "gif --gif-mode resize --resize 75 --auto-run" },
            @{ Id = "colors"; Label = [string]([char]0x51CF) + [char]0x8272 + " 128"; Args = "gif --gif-mode reduce_colors --auto-run" },
            @{ Id = "speed2"; Label = "2" + [char]0x500D + [char]0x901F; Args = "gif --gif-mode speed --speed 2 --auto-run" },
            @{ Id = "speed05"; Label = [string]([char]0x534A) + [char]0x901F + " 0.5x"; Args = "gif --gif-mode speed --speed 0.5 --auto-run" },
            @{ Id = "reverse"; Label = [string]([char]0x5012) + [char]0x653E; Args = "gif --gif-mode reverse --auto-run" },
            @{ Id = "trim"; Label = [string]([char]0x88C1) + [char]0x900F + [char]0x660E + [char]0x8FB9; Args = "gif --gif-mode trim --auto-run" },
            @{ Id = "wm"; Label = [string]([char]0x6C34) + [char]0x5370; Args = "gif --gif-mode watermark --auto-run" },
            @{ Id = "extract"; Label = [string]([char]0x62C6) + [char]0x5E27 + [char]0x5BFC + [char]0x51FA; Args = "gif --gif-mode extract --auto-run" }
        )
    }
)

function Remove-ImgBatchMenuKey {
    param([Microsoft.Win32.RegistryKey]$Hive, [string]$Rel)
    try { $Hive.DeleteSubKeyTree($Rel, $false) } catch {}
}

function Clear-ImgBatchContextMenu {
    param([Microsoft.Win32.RegistryKey]$Hive)

    $flat = @(
        "ImgBatch", "ImgBatchMore", "ImgBatchSep",
        "ImgBatchCompress", "ImgBatchConvert", "ImgBatchRename",
        "ImgBatchWatermark", "ImgBatchTrim", "ImgBatchNormalize", "ImgBatchInspect", "ImgBatchGif"
    )
    $classRoots = @(
        "*", "Directory", "Directory\Background",
        ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".ico", ".heic", ".heif", ".avif",
        "SystemFileAssociations\image"
    )
    foreach ($cr in $classRoots) {
        foreach ($name in $flat) {
            Remove-ImgBatchMenuKey $Hive "Software\Classes\$cr\shell\$name"
        }
    }

    $storeBase = "Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell"
    foreach ($menu in $script:ActionMenus) {
        Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.$($menu.Id)"
        Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.dir.$($menu.Id)"
        foreach ($item in $menu.Items) {
            Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.$($menu.Id).$($item.Id)"
            Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.dir.$($menu.Id).$($item.Id)"
        }
    }
    Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.convert"
    Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.dir.convert"
    Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.more"
    Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.dir.more"
    Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.misc"
    Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.dir.misc"
    foreach ($f in $script:ConvertFormats) {
        Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.convert.$($f.Id)"
        Remove-ImgBatchMenuKey $Hive "$storeBase\ImgBatch.dir.convert.$($f.Id)"
    }
}

function Write-ImgBatchStoreVerb {
    param(
        [Microsoft.Win32.RegistryKey]$Hive,
        [string]$StoreId,
        [string]$Label,
        [string]$CommandLine
    )
    $key = $Hive.CreateSubKey("Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\$StoreId")
    $key.SetValue("MUIVerb", $Label)
    $key.SetValue("Icon", "$script:ImgBatchExePath,0")
    $key.SetValue("MultiSelectModel", "Player")
    $cmd = $key.CreateSubKey("command")
    $cmd.SetValue("", $CommandLine)
    $cmd.Close()
    $key.Close()
}

function Write-ImgBatchStoreParent {
    param(
        [Microsoft.Win32.RegistryKey]$Hive,
        [string]$StoreId,
        [string]$Label,
        [string]$SubCommands
    )
    $key = $Hive.CreateSubKey("Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\$StoreId")
    $key.SetValue("MUIVerb", $Label)
    $key.SetValue("Icon", "$script:ImgBatchExePath,0")
    $key.SetValue("SubCommands", $SubCommands)
    $key.Close()
}

function Write-ImgBatchClassCascade {
    param(
        [Microsoft.Win32.RegistryKey]$Hive,
        [string]$ClassRoot,
        [string]$ShellKey,
        [string]$Label,
        [string]$SubCommands
    )
    $key = $Hive.CreateSubKey("Software\Classes\$ClassRoot\shell\$ShellKey")
    $key.SetValue("MUIVerb", "ImgBatch $Label")
    $key.SetValue("Icon", "$script:ImgBatchExePath,0")
    $key.SetValue("SubCommands", $SubCommands)
    $key.Close()
}

function Get-ImgBatchLeafSubCommands {
    param(
        [string]$MenuId,
        [switch]$ForDirectory
    )
    $menu = $script:ActionMenus | Where-Object { $_.Id -eq $MenuId } | Select-Object -First 1
    if (-not $menu) { return "" }
    $prefix = if ($ForDirectory) { "ImgBatch.dir" } else { "ImgBatch" }
    return ($menu.Items | ForEach-Object { "$prefix.$MenuId.$($_.Id)" }) -join ";"
}

$script:TopLevelMenuShellKeys = [ordered]@{
    compress   = "ImgBatchCompress"
    convert    = "ImgBatchConvert"
    rename     = "ImgBatchRename"
    watermark  = "ImgBatchWatermark"
    trim       = "ImgBatchTrim"
    normalize  = "ImgBatchNormalize"
    inspect    = "ImgBatchInspect"
    gif        = "ImgBatchGif"
}

function Register-ImgBatchActionMenu {
    param(
        [Microsoft.Win32.RegistryKey]$Hive,
        [hashtable]$Menu,
        [string]$FilePlaceholder,
        [string]$DirPlaceholder
    )
    $fileSub = ($Menu.Items | ForEach-Object { "ImgBatch.$($Menu.Id).$($_.Id)" }) -join ";"
    $dirSub = ($Menu.Items | ForEach-Object { "ImgBatch.dir.$($Menu.Id).$($_.Id)" }) -join ";"

    Write-ImgBatchStoreParent $Hive "ImgBatch.$($Menu.Id)" $Menu.Label $fileSub
    Write-ImgBatchStoreParent $Hive "ImgBatch.dir.$($Menu.Id)" $Menu.Label $dirSub

    foreach ($item in $Menu.Items) {
        $fileCmd = "`"$script:ImgBatchExePath`" --quick $($item.Args) `"$FilePlaceholder`""
        $dirCmd = "`"$script:ImgBatchExePath`" --quick $($item.Args) `"$DirPlaceholder`""
        Write-ImgBatchStoreVerb $Hive "ImgBatch.$($Menu.Id).$($item.Id)" $item.Label $fileCmd
        Write-ImgBatchStoreVerb $Hive "ImgBatch.dir.$($Menu.Id).$($item.Id)" $item.Label $dirCmd
    }
}

function Register-ImgBatchContextMenu {
    param(
        [Microsoft.Win32.RegistryKey]$Hive,
        [string]$ExePath
    )
    $script:ImgBatchExePath = $ExePath
    $convertLabel = [string]([char]0x683C) + [char]0x5F0F + [char]0x8F6C + [char]0x6362
    $convertToLabel = [string]([char]0x8F6C) + [char]0x4E3A

    Clear-ImgBatchContextMenu -Hive $Hive

    foreach ($menu in $script:ActionMenus) {
        Register-ImgBatchActionMenu -Hive $Hive -Menu $menu -FilePlaceholder "%1" -DirPlaceholder "%V"
    }

    $fileConvertSub = ($script:ConvertFormats | ForEach-Object { "ImgBatch.convert.$($_.Id)" }) -join ";"
    $dirConvertSub = ($script:ConvertFormats | ForEach-Object { "ImgBatch.dir.convert.$($_.Id)" }) -join ";"
    Write-ImgBatchStoreParent $Hive "ImgBatch.convert" $convertLabel $fileConvertSub
    Write-ImgBatchStoreParent $Hive "ImgBatch.dir.convert" $convertLabel $dirConvertSub

    foreach ($f in $script:ConvertFormats) {
        $label = "$convertToLabel $($f.Label)"
        Write-ImgBatchStoreVerb $Hive "ImgBatch.convert.$($f.Id)" $label "`"$script:ImgBatchExePath`" --quick convert --format $($f.Ext) --auto-run `"%1`""
        Write-ImgBatchStoreVerb $Hive "ImgBatch.dir.convert.$($f.Id)" $label "`"$script:ImgBatchExePath`" --quick convert --format $($f.Ext) --auto-run `"%V`""
    }

    # Each feature is its own top-level context-menu entry (each may have a submenu).
    $registerOrder = @("compress", "convert", "rename", "watermark", "trim", "normalize", "inspect", "gif")
    $classRoots = @("*", "Directory", "Directory\Background", "SystemFileAssociations\image")
    foreach ($cr in $classRoots) {
        $forDir = $cr -like "Directory*"
        foreach ($menuId in $registerOrder) {
            if ($menuId -eq "convert") {
                $convertSub = if ($forDir) { $dirConvertSub } else { $fileConvertSub }
                Write-ImgBatchClassCascade -Hive $Hive -ClassRoot $cr -ShellKey "ImgBatchConvert" -Label $convertLabel -SubCommands $convertSub
                continue
            }
            $menu = $script:ActionMenus | Where-Object { $_.Id -eq $menuId } | Select-Object -First 1
            if (-not $menu) { continue }
            $shellKey = $script:TopLevelMenuShellKeys[$menuId]
            $sub = Get-ImgBatchLeafSubCommands -MenuId $menuId -ForDirectory:$forDir
            Write-ImgBatchClassCascade -Hive $Hive -ClassRoot $cr -ShellKey $shellKey -Label $menu.Label -SubCommands $sub
        }
    }
}
