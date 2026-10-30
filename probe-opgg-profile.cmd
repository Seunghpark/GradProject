@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
if not exist ".venv\Scripts\python.exe" (
  echo Python dependencies are missing. Run setup.ps1 first.
  exit /b 1
)
echo Read-only OP.GG profile check for Molybdite#KR1, Korea. No Riot key is sent.
".venv\Scripts\python.exe" backend\scripts\probe_opgg_profile.py --riot-id "Molybdite#KR1" --region KR
exit /b %ERRORLEVEL%
