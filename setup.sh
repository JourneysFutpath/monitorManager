#!/bin/bash

# Ensure the script is run as a user (not root)
if [ "$(id -u)" -eq 0 ]; then
    echo "Please do not run this script as root. Exiting."
    exit 1
fi

# Update package list and install necessary dependencies
echo "Updating package list..."
sudo apt update

echo "Installing dependencies..."
sudo apt install -y python3 python3-pip python3-pyqt5 x11-xserver-utils

# Install Python packages
echo "Installing Python dependencies..."
pip3 install --user PyQt5

# Make sure the application directory exists
APP_DIR="$HOME/monitor-layout-manager"
if [ ! -d "$APP_DIR" ]; then
    echo "Creating application directory..."
    mkdir -p "$APP_DIR"
fi

# Clone the repository (if not already done)
if [ ! -d "$APP_DIR/.git" ]; then
    echo "Cloning the repository..."
    git clone https://github.com/your-username/monitor-layout-manager.git "$APP_DIR"
fi

# Set up permissions
echo "Setting up file permissions..."
chmod +x "$APP_DIR/setup.sh"
chmod +x "$APP_DIR/main.py"

# Display completion message
echo "Setup completed! You can now run the application using:"
echo "python3 $APP_DIR/main.py"

# End of script
exit 0

