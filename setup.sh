#!/bin/bash
set -e

echo "=== Ivar Setup Script ==="
echo "Setting up your Raspberry Pi for Ivar..."
echo

# Update system
echo "[1/5] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Pi AI Camera (IMX500) firmware and tools
echo "[2/5] Installing AI Camera firmware (imx500-all)..."
sudo apt install -y imx500-all

# Install picamera2 and Python dependencies
echo "[3/5] Installing picamera2 and Python tools..."
sudo apt install -y python3-picamera2 python3-libcamera python3-venv python3-pip

# Create virtual environment with system packages access
# (--system-site-packages is needed because picamera2 is installed via apt)
echo "[4/5] Creating Python virtual environment..."
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install Python dependencies
echo "[5/5] Installing Python dependencies..."
pip install -r requirements.txt

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo
    echo "Created .env file from template."
fi

# Create captures directory
mkdir -p captures

echo
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo
echo "  Next steps:"
echo "  1. Edit .env and add your ANTHROPIC_API_KEY"
echo "  2. Reboot your Pi (required for camera firmware):"
echo "       sudo reboot"
echo "  3. After reboot, start Ivar:"
echo "       cd ~/ivar"
echo "       source venv/bin/activate"
echo "       python main.py"
echo
