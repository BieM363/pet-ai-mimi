@echo off
cd /d "%~dp0"

:: Jalankan Mimi secara instan di background tanpa popup UAC (seperti IDM)
where pythonw >nul 2>&1
if %errorlevel% == 0 (
    start "" pythonw main.py
) else (
    start "" python main.py
)
