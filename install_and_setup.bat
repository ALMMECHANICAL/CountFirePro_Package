@echo off
title CountFire Pro - Installation

echo ====================================================
echo     COUNTFIRE PRO DESKTOP - AUTOMATIC INSTALLER
echo ====================================================
echo.
echo This will install CountFire Pro Desktop on your system.
echo.
pause

echo.
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.11 or newer from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Python found!
echo.
echo Installing required dependencies...
echo This may take a few minutes...
echo.

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies.
    echo Please run as Administrator or check your internet connection.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo     INSTALLATION COMPLETE!
echo ====================================================
echo.
echo CountFire Pro Desktop has been successfully installed.
echo.
echo To run the application:
echo   - Double-click "run_countfire_pro.bat"
echo   - Or run: python desktop_app.py
echo.
echo Creating desktop shortcut...

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\CountFire Pro.lnk'); $Shortcut.TargetPath = '%CD%\run_countfire_pro.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Save()"

echo Desktop shortcut created!
echo.
pause