# MAGUS RPG - Environment Setup Script for Windows (PowerShell)
# This script sets up a Python virtual environment and installs all dependencies
# Run: powershell -ExecutionPolicy Bypass -File setup_env.ps1

param(
    [switch]$SkipDevDeps = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"

Write-Host "================================================" -ForegroundColor $Yellow
Write-Host "MAGUS RPG - Environment Setup (Windows PowerShell)" -ForegroundColor $Yellow
Write-Host "================================================" -ForegroundColor $Yellow
Write-Host ""

# Check if Python 3.13 is installed
Write-Host "Checking Python version..." -ForegroundColor $Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor $Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor $Red
    Write-Host "Please install Python 3.13 and add it to PATH."
    exit 1
}
Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor $Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Removing it..." -ForegroundColor $Yellow
    Remove-Item -Recurse -Force -Path venv | Out-Null
}

try {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor $Green
} catch {
    Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor $Red
    exit 1
}
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor $Yellow
try {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "✓ Virtual environment activated" -ForegroundColor $Green
} catch {
    Write-Host "ERROR: Failed to activate virtual environment." -ForegroundColor $Red
    exit 1
}
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor $Yellow
try {
    python -m pip install --upgrade pip setuptools wheel | Out-Null
    Write-Host "✓ pip upgraded" -ForegroundColor $Green
} catch {
    Write-Host "WARNING: Failed to upgrade pip, continuing anyway..." -ForegroundColor $Yellow
}
Write-Host ""

# Install main dependencies
Write-Host "Installing dependencies..." -ForegroundColor $Yellow
try {
    pip install pygame pyside6 pydantic
    Write-Host "✓ Main dependencies installed" -ForegroundColor $Green
} catch {
    Write-Host "ERROR: Failed to install dependencies." -ForegroundColor $Red
    exit 1
}
Write-Host ""

# Ask about dev dependencies
if (-not $SkipDevDeps) {
    $response = Read-Host "Do you want to install development dependencies? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "Installing development dependencies..." -ForegroundColor $Yellow
        try {
            pip install black ruff mypy pytest pytest-cov mkdocs-material pre-commit
            Write-Host "✓ Development dependencies installed" -ForegroundColor $Green
        } catch {
            Write-Host "WARNING: Some development dependencies failed to install." -ForegroundColor $Yellow
        }
        Write-Host ""
    }
}

Write-Host "================================================" -ForegroundColor $Green
Write-Host "Setup completed successfully!" -ForegroundColor $Green
Write-Host "================================================" -ForegroundColor $Green
Write-Host ""

Write-Host "To activate the environment in the future, run:" -ForegroundColor $Yellow
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "To verify the installation, you can run:" -ForegroundColor $Yellow
Write-Host "  python MAGUS_pygame\main.py"
Write-Host ""
