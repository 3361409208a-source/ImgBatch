$ErrorActionPreference = "Stop"
Push-Location frontend
npm install
npm run build
Pop-Location
Write-Host "Frontend built -> frontend/dist"
