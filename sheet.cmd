@echo off
setlocal
pushd "%~dp0" || exit /b 1
"%~dp0.venv\Scripts\python.exe" -m scripts.build_sheet %*
set "babbdExit=%errorlevel%"
popd
exit /b %babbdExit%
