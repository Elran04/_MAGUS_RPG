@echo off
REM MAGUS RPG - Environment Setup Script for Windows (Batch)
REM This script sets up a Python virtual environment and installs all dependencies

setlocal enabledelayedexpansion

REM Colors simulation
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "NC=[0m"

echo.
echo ================================================
echo MAGUS RPG - Environment Setup (Windows)
echo ================================================
echo.

REM Check if Python 3.13 is installed
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.13 and add it to PATH.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found: Python %PYTHON_VERSION%
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Removing it...
    rmdir /s /q venv >nul 2>&1
)

python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)
echo Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
echo pip upgraded
echo.

REM Install main dependencies
echo Installing dependencies...
pip install pygame pyside6 pydantic
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo Main dependencies installed
echo.

REM Ask about dev dependencies
set /p DEV_DEPS="Do you want to install development dependencies? (y/n): "
if /i "%DEV_DEPS%"=="y" (
    echo Installing development dependencies...
    pip install black ruff mypy pytest pytest-cov mkdocs-material pre-commit
    if errorlevel 1 (
        echo WARNING: Some development dependencies failed to install.
    ) else (
        echo Development dependencies installed
    )
    echo.
)

echo ================================================
echo Setup completed successfully!
echo ================================================
echo.

echo To activate the environment in the future, run:
echo   venv\Scripts\activate.bat
echo.
echo To verify the installation, you can run:
echo   python MAGUS_pygame\main.py
echo.

pause
