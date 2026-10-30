@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Dependencies are missing. Run setup first.
  exit /b 1
)
if not exist ".tmp" mkdir ".tmp"
set "TEMP=%CD%\.tmp"
set "TMP=%CD%\.tmp"
set "PYTHONUTF8=1"
echo Running mocked API, collector and model tests. Your running server stays open.
".venv\Scripts\python.exe" -m pytest -q --basetemp=.tmp/pytest-cli
exit /b %ERRORLEVEL%
