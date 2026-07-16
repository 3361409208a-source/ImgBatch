# Register ImgBatch cascading quick-action context menus for the current user (HKCU).
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

function Set-ShellCascade([string]$ClassRoot, [string]$ArgToken) {
    # Use .NET so "*" is not treated as a PowerShell wildcard.
    $base = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Software\Classes\$ClassRoot\shell\ImgBatch")
    $base.SetValue("", "ImgBatch")
    $base.SetValue("MUIVerb", "ImgBatch")
    $base.SetValue("Icon", "$ExePath,0")
    $base.SetValue("SubCommands", "")

    foreach ($a in $actions) {
        $verb = $base.CreateSubKey("shell\$($a.Id)")
        $verb.SetValue("MUIVerb", $a.Label)
        $verb.SetValue("Icon", "$ExePath,0")
        $verb.SetValue("MultiSelectModel", "Player")
        $cmd = $verb.CreateSubKey("command")
        $cmd.SetValue("", "`"$ExePath`" --quick $($a.Id) $ArgToken")
        $cmd.Close()
        $verb.Close()
    }
    $base.Close()
}

$targets = @(
    @{ Root = "*"; Arg = '"%1"' },
    @{ Root = "Directory"; Arg = '"%V"' },
    @{ Root = "Directory\Background"; Arg = '"%V"' },
    @{ Root = ".png"; Arg = '"%1"' },
    @{ Root = ".jpg"; Arg = '"%1"' },
    @{ Root = ".jpeg"; Arg = '"%1"' },
    @{ Root = ".webp"; Arg = '"%1"' },
    @{ Root = ".gif"; Arg = '"%1"' },
    @{ Root = ".bmp"; Arg = '"%1"' },
    @{ Root = ".tif"; Arg = '"%1"' },
    @{ Root = ".tiff"; Arg = '"%1"' },
    @{ Root = ".ico"; Arg = '"%1"' },
    @{ Root = "SystemFileAssociations\image"; Arg = '"%1"' }
)

foreach ($t in $targets) {
    Set-ShellCascade -ClassRoot $t.Root -ArgToken $t.Arg
}

Write-Host "Registered ImgBatch context menus -> $ExePath"
