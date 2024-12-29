#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Get the current folder name
current_folder=$(basename "$(pwd)")
venv_dir=".venv_${current_folder}"

# Create the virtual environment
echo "Creating a virtual environment in $venv_dir..."
python3 -m venv "$venv_dir"

# Activate the virtual environment
echo "Activating the virtual environment..."
source "$venv_dir/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Skipping dependency installation."
fi

echo "Virtual environment setup is complete in $venv_dir. To activate, run:"
echo "source $venv_dir/bin/activate"
