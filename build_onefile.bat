@echo off
cd /d "%~dp0"
echo Build onefile (1 seul exe, demarrage plus lent)...
py -3 -m PyInstaller Reframed.spec --noconfirm
if errorlevel 1 exit /b 1
echo.
echo OK : dist\Reframed.exe
pause
