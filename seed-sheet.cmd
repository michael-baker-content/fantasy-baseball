@echo off
"%~dp0.venv\Scripts\python.exe" "%~dp0seed_sheet.py" %*
exit /b %errorlevel%
