@echo off
cd /d "%~dp0"
REM Mode dev : console, sans admin/instance unique, probe qt-mcp pour l'agent Cursor
set QT_MCP_PROBE=1
py -3 main.py --no-admin --no-single --qt-mcp
pause
