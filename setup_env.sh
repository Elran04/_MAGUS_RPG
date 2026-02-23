#!/bin/bash

# MAGUS RPG - Environment Setup Script
# This script sets up a Python virtual environment and installs all dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================================${NC}"
echo -e "${YELLOW}MAGUS RPG - Environment Setup${NC}"
echo -e "${YELLOW}================================================${NC}\n"

# Check if Python 3.13 is installed
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3.13 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3.13 is not installed.${NC}"
    echo "Please install Python 3.13 and try again."
    exit 1
fi

PYTHON_VERSION=$(python3.13 --version)
echo -e "${GREEN}✓ Found: $PYTHON_VERSION${NC}\n"

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Removing it...${NC}"
    rm -rf venv
fi

python3.13 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}\n"

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}\n"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓ pip upgraded${NC}\n"

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install pygame pyside6 pydantic
echo -e "${GREEN}✓ Main dependencies installed${NC}\n"

# Install development dependencies (optional)
read -p "Do you want to install development dependencies? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    pip install black ruff mypy pytest pytest-cov mkdocs-material pre-commit
    echo -e "${GREEN}✓ Development dependencies installed${NC}\n"
fi

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}================================================${NC}\n"

echo -e "${YELLOW}To activate the environment in the future, run:${NC}"
echo "source venv/bin/activate"
echo ""
echo -e "${YELLOW}To verify the installation, you can run:${NC}"
echo "python MAGUS_pygame/main.py"
