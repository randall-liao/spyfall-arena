#!/bin/bash
# scripts/setup-git-hooks.sh

set -e

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install Poetry first."
    exit 1
fi

echo "Installing dependencies..."
poetry install

echo "Setting up pre-commit hooks..."
# Try to unset core.hooksPath if set, just in case
git config --unset-all core.hooksPath || true
poetry run pre-commit install

echo "Pre-commit hooks installed successfully!"
