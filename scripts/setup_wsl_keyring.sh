#!/bin/bash

# Setup script for ensuring keyring works in WSL
# This script installs system dependencies and sets up environment variables.

set -e

echo "Checking for system dependencies..."

# Function to check if a package is installed
is_installed() {
    dpkg -l "$1" &> /dev/null
}

MISSING_PACKAGES=()

if ! is_installed "gnome-keyring"; then
    MISSING_PACKAGES+=("gnome-keyring")
fi

if ! is_installed "dbus-x11"; then
    MISSING_PACKAGES+=("dbus-x11")
fi

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "Installing missing packages: ${MISSING_PACKAGES[*]}"
    sudo apt-get update
    sudo apt-get install -y "${MISSING_PACKAGES[@]}"
else
    echo "All system dependencies are installed."
fi

# Environment Setup Instructions
echo ""
echo "To use keyring in WSL, you must have a DBus session active."
echo "Add the following to your ~/.bashrc or ~/.zshrc if not already present:"
echo ""
echo 'export XDG_RUNTIME_DIR=/run/user/$(id -u)'
echo 'if [ ! -d "$XDG_RUNTIME_DIR" ]; then'
echo '    sudo mkdir -p "$XDG_RUNTIME_DIR"'
echo '    sudo chown $(id -u):$(id -g) "$XDG_RUNTIME_DIR"'
echo '    chmod 700 "$XDG_RUNTIME_DIR"'
echo 'fi'
echo ""
echo 'if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then'
echo '    eval $(dbus-launch --sh-syntax)'
echo 'fi'
echo ""
echo "# Unlock keyring (optional, requires password)"
echo '# echo "your_password" | gnome-keyring-daemon --unlock'
echo '# gnome-keyring-daemon --start --components=secrets'
