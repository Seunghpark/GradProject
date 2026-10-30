$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
New-Item -ItemType Directory -Force -Path '.tmp' | Out-Null
$env:TEMP = (Resolve-Path '.tmp').Path
$env:TMP = $env:TEMP
$env:PYTHONUTF8 = '1'
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed. Install Python 3.11 or later.' }
}
& '.venv/Scripts/python.exe' -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw 'Could not prepare pip.' }
& '.venv/Scripts/python.exe' -m pip install -r backend/requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
$packageManager = Get-Command pnpm -ErrorAction SilentlyContinue
$bundledPnpm = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm.cmd'
if ($packageManager) { $packageManagerPath = $packageManager.Source }
elseif (Test-Path -LiteralPath $bundledPnpm) { $packageManagerPath = $bundledPnpm }
else { $packageManagerPath = (Get-Command npm -ErrorAction Stop).Source }
Push-Location frontend
try {
    & $packageManagerPath install --ignore-scripts
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    New-Item -ItemType Directory -Force -Path 'dist/assets' | Out-Null
    & $packageManagerPath run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally { Pop-Location }
if (-not (Test-Path -LiteralPath 'backend/data/model.json')) {
    & '.venv/Scripts/python.exe' backend/scripts/generate_synthetic_training.py --count 300
    if ($LASTEXITCODE -ne 0) { throw 'Synthetic fixture generation failed.' }
    & '.venv/Scripts/python.exe' backend/scripts/train_model.py --input backend/data/synthetic_training.jsonl --algorithm mlp
    if ($LASTEXITCODE -ne 0) { throw 'Demo model training failed.' }
}
Write-Host 'Setup complete. Run ./start.cmd and open http://127.0.0.1:8000'


