#!/bin/bash
set -e

# Setup Runtime Directory for DBus/Keyring
export XDG_RUNTIME_DIR=/run/user/$(id -u)
if [ ! -d "$XDG_RUNTIME_DIR" ]; then
    sudo mkdir -p "$XDG_RUNTIME_DIR"
    sudo chown $(id -u):$(id -g) "$XDG_RUNTIME_DIR"
    chmod 700 "$XDG_RUNTIME_DIR"
fi

# Run the test inside a dbus session
# We use --sh-syntax to export variables for the current shell
eval $(dbus-launch --sh-syntax)

echo "DBUS_SESSION_BUS_ADDRESS: $DBUS_SESSION_BUS_ADDRESS"

# Start and unlock gnome-keyring-daemon
# We attempt to unlock with 'devuser' which matches the user's login based on sudo usage
echo "Starting gnome-keyring-daemon..."
eval $(gnome-keyring-daemon --start --components=secrets)
export SSH_AUTH_SOCK

# Unlock the default keyring (usually 'login') or create a default one
# This echo pipes the password to stdin of the daemon
echo -n "devuser" | gnome-keyring-daemon --unlock || echo "Failed to unlock keyring (might already be unlocked or different password)"

# Check if we can talk to the secret service
echo "Checking secret service reachability..."
./.venv/bin/python -c "import secretstorage; print('SecretStorage backend reachable.')" || echo "SecretStorage check failed."

# Run the specific test
echo "Running E2E Keyring Test..."
./.venv/bin/pytest tests/e2e/test_keyring_integration.py -v -s

# Cleanup
kill $DBUS_SESSION_BUS_PID
