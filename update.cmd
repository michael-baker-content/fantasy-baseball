@echo off
"%~dp0.venv\Scripts\python.exe" "%~dp0update_site.py" %*
exit /b %errorlevel%
