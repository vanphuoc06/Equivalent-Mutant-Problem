#!/bin/bash

# NSEV Environment Setup Script
echo "--- Initializing NSEV Environment ---"

# 1. Update and install basic dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev

# 2. Install Python requirements (including Z3 and OpenAI)
echo "Installing Python libraries..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Verify Z3 Solver installation (Phase 6 backend)
python3 -c "import z3; print('Z3 Version:', z3.get_version_string())"

# 4. Create .env file template
if [ ! -f .env ]; then
    echo "Creating .env template..."
    echo "OPENAI_API_KEY=your_api_key_here" > .env
    echo "ANTHROPIC_API_KEY=your_api_key_here" >> .env
fi

echo "--- Setup Complete ---"
echo "Please update your .env file with your API keys before running main.py."
