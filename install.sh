#!/usr/bin/env bash
# First-time setup script for ai-feedback
# Run from project root: ./install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Setting up ai-feedback..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate and install
echo "Installing package..."
source .venv/bin/activate
pip install -e . -q

# Copy .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "  -> Edit .env to add your OPENAI_API_KEY or LM Studio config"
else
    echo ".env already exists."
fi

# Create output directory
mkdir -p output
echo "Output directory ready: output/"

echo ""
echo "Done! Next steps:"
echo "  1. Activate the venv: source .venv/bin/activate"
echo "  2. Edit .env with your API key or LLM_BASE_URL for LM Studio"
echo "  3. Run: feedback generate -i examples/sample-notes.txt -c \"John Doe\""
