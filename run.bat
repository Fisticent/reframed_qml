@echo off
cd /d "%~dp0"
REM run_dev.bat = code source a jour | run.bat = exe dist (recompiler apres modifs)
if exist "dist\Reframed\Reframed.exe" (
    start "" "dist\Reframed\Reframed.exe"
) else if exist "dist\Reframed.exe" (
    start "" "dist\Reframed.exe"
) else (
    pythonw main.py
)
