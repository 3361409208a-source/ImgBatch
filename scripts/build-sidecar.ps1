$ErrorActionPreference = "Stop"
$Triple = "x86_64-pc-windows-msvc"
$OutDir = "src-tauri/binaries"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
pyinstaller imgbatch-api.spec --noconfirm --clean
Copy-Item "dist/imgbatch-api.exe" "$OutDir/imgbatch-api-$Triple.exe" -Force
Write-Host "Sidecar -> $OutDir/imgbatch-api-$Triple.exe"
