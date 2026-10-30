@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
if not exist ".venv\Scripts\python.exe" (
  echo Python dependencies are missing. Run setup.ps1 first.
  exit /b 1
)
echo Read-only OP.GG tool discovery. No Riot key or player information is sent.
".venv\Scripts\python.exe" backend\scripts\probe_opgg.py
exit /b %ERRORLEVEL%
