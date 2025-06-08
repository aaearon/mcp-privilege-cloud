@echo off
REM CyberArk MCP Server Launcher for Windows
REM This batch file ensures proper encoding and environment setup

cd /d "%~dp0"

REM Set UTF-8 code page
chcp 65001 >nul 2>&1

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the server
python run_server_windows.py

pause