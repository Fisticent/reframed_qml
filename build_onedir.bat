@echo off
cd /d "%~dp0"
echo Build onedir (demarrage rapide)...
py -3 -m PyInstaller Reframed-onedir.spec --noconfirm
if errorlevel 1 exit /b 1
echo.
echo OK : dist\Reframed\Reframed.exe
pause
