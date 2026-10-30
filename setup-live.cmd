@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" backend\scripts\setup_live_client.py
exit /b %ERRORLEVEL%
