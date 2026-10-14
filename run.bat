@echo off
:: ==============================================================================
:: Mimi Virtual Pixel Cat AI Companion
:: Creator / Author: BieM363 (https://github.com/BieM363)
:: GitHub Repository: https://github.com/BieM363/pet-ai-mimi
:: ==============================================================================

cd /d "%~dp0"

:: Jalankan Mimi secara instan di background tanpa popup UAC (seperti IDM)
where pythonw >nul 2>&1
if %errorlevel% == 0 (
    start "" pythonw main.py
) else (
    start "" python main.py
)
