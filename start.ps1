param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) { throw 'Run ./setup.ps1 first.' }
if (-not (Test-Path -LiteralPath 'frontend/dist/index.html')) { throw 'Frontend is not built. Run ./setup.ps1 first.' }
$env:PYTHONUTF8 = '1'
Write-Host "LolAi.gg: http://127.0.0.1:$Port (Ctrl+C to stop)"
& '.venv/Scripts/python.exe' -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port $Port
