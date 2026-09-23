@echo off
"%~dp0.venv\Scripts\python.exe" "%~dp0build_sheet.py" %*
exit /b %errorlevel%
