@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Dependencies are missing. Run setup.ps1 first.
  exit /b 1
)
if not exist "frontend\dist\index.html" (
  echo Frontend build is missing. Run setup.ps1 first.
  exit /b 1
)
set "PYTHONUTF8=1"
echo LolAi.gg: http://127.0.0.1:8000 [Ctrl+C to stop]
".venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
exit /b %ERRORLEVEL%
