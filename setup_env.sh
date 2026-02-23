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

# Check if Python 3.9+ is installed
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_CMD=""
PYTHON_VERSION=""

for version in python3.13 python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v $version &> /dev/null; then
        PYTHON_VERSION=$($version --version 2>&1)
        # Extract version number (e.g., "3.9" from "Python 3.9.18")
        VERSION_NUM=$(echo "$PYTHON_VERSION" | grep -oP 'Python \K[\d.]+' | cut -d. -f1,2)
        
        # Check if we have a valid version number
        if [ ! -z "$VERSION_NUM" ]; then
            # Simple comparison: 3.9+
            MAJOR=$(echo "$VERSION_NUM" | cut -d. -f1)
            MINOR=$(echo "$VERSION_NUM" | cut -d. -f2)
            
            if [ "$MAJOR" = "3" ] && [ "$MINOR" -ge "9" ]; then
                PYTHON_CMD=$version
                echo -e "${GREEN}✓ Found: $PYTHON_VERSION${NC}"
                echo ""
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}ERROR: Python 3.9 or higher is not installed.${NC}"
    echo "Please install Python 3.9+ and try again."
    exit 1
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Removing it...${NC}"
    rm -rf venv
fi

$PYTHON_CMD -m venv venv
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
