@echo off
title Network Device Discovery Tool
echo Starting Network Device Discovery Tool...

:: Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment (venv)...
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment (.venv)...
    call .venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not detected. Running using system Python.
)

:: Run application
python -m app.main

echo.
echo Application finished.
pause
