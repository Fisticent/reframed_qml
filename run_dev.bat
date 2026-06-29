@echo off
cd /d "%~dp0"
REM Mode dev avec console (debug) + sans élévation admin / sans instance unique
py -3 main.py --no-admin --no-single
pause
