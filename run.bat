@echo off
title "TIDAL & Billboard Media Intel Center"

echo ===================================================
echo   TIDAL ^& Billboard Combined Setup
echo ===================================================
echo.

set PYTHON_CMD=python
py --version >nul 2>&1
if not errorlevel 1 (
    py -3.12 --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=py -3.12
    ) else (
        py -3.11 --version >nul 2>&1
        if not errorlevel 1 (
            set PYTHON_CMD=py -3.11
        ) else (
            py -3.10 --version >nul 2>&1
            if not errorlevel 1 (
                set PYTHON_CMD=py -3.10
            )
        )
    )
) else (
    python --version >nul 2>&1
    if errorlevel 1 goto :nopython
)

if exist venv goto :activate_venv

echo [STATUS] Creating Python virtual environment (venv) using %PYTHON_CMD%...
%PYTHON_CMD% -m venv venv
if not exist venv goto :novenv
echo [STATUS] Virtual environment created successfully.

:activate_venv
echo [STATUS] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 goto :noactivate

echo [STATUS] Upgrading pip...
python -m pip install --upgrade pip

echo [STATUS] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 goto :nodeps

echo.
echo [STATUS] Setup completed successfully!
echo [STATUS] Launching UI...
echo ===================================================
echo.

python app.py
goto :eof

:nopython
echo [ERROR] Python is not installed or not in PATH.
echo Please install Python 3.8+ and try again.
pause
exit /b 1

:novenv
echo [ERROR] Failed to create virtual environment.
pause
exit /b 1

:noactivate
echo [ERROR] Failed to activate virtual environment.
pause
exit /b 1

:nodeps
echo [ERROR] Failed to install dependencies.
pause
exit /b 1
