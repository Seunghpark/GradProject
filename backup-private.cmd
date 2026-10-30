@echo off
setlocal
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup first. Python environment is missing.
  popd
  exit /b 1
)
".venv\Scripts\python.exe" backend\scripts\backup_private.py
set "backup_result=%errorlevel%"
popd
exit /b %backup_result%
