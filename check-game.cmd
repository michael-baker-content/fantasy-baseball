@echo off
setlocal
pushd "%~dp0" || exit /b 1
"%~dp0.venv\Scripts\python.exe" -m scripts.check_game %*
set "babbdExit=%errorlevel%"
popd
exit /b %babbdExit%
