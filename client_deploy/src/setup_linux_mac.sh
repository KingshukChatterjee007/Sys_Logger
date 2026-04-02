#!/bin/bash

# =====================================
# Sys_Logger Client - Linux/Mac Setup Script
# Installs PM2, sets up Python venv, starts the client,
# and configures auto-start on system boot.
# =====================================

set -e

echo ""
echo "======================================"
echo "  Sys_Logger Client - Linux/Mac Setup "
echo "======================================"
echo ""

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"

# ==========================================
# Step 1: Check Prerequisites
# ==========================================
echo "[Step 1/5] Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "  ERROR: Node.js not found!"
    echo "  Install it:"
    echo "    Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs"
    echo "    Mac: brew install node"
    exit 1
fi
echo "  ✅ Node.js found: $(node -v)"

# Check/Install PM2
if ! command -v pm2 &> /dev/null; then
    echo "  📥 Installing PM2..."
    sudo npm install -g pm2
fi
echo "  ✅ PM2 found"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  ERROR: Python3 not found!"
    exit 1
fi
echo "  ✅ Python3 found: $(python3 --version)"

# ==========================================
# Step 2: Setup Python Virtual Environment
# ==========================================
echo ""
echo "[Step 2/5] Setting up Python..."

if [ ! -d "$DEPLOY_DIR/venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv "$DEPLOY_DIR/venv"
fi
echo "  ✅ Python venv ready"

# ==========================================
# Step 3: Install Dependencies
# ==========================================
echo ""
echo "[Step 3/5] Installing dependencies..."

source "$DEPLOY_DIR/venv/bin/activate"
pip install -r "$DEPLOY_DIR/requirements.txt" --quiet
echo "  ✅ Dependencies installed"

# ==========================================
# Step 4: Start Client via PM2
# ==========================================
echo ""
echo "[Step 4/5] Starting client via PM2..."

# Create logs directory
mkdir -p "$DEPLOY_DIR/logs"

# Stop any existing instance
pm2 delete sys-logger-client 2>/dev/null || true

# Start with ecosystem config, using venv Python
cd "$DEPLOY_DIR"
pm2 start ecosystem.config.js

# Save the process list (so pm2 resurrect can restore it)
pm2 save --force

echo "  ✅ Client is running"

# ==========================================
# Step 5: Configure Auto-Start on Boot
# ==========================================
echo ""
echo "[Step 5/5] Configuring auto-start on boot..."

# Generate the startup script (works on systemd, upstart, launchd)
# pm2 startup outputs a command that needs to be run with sudo
STARTUP_CMD=$(pm2 startup 2>&1 | grep "sudo" | head -1)

if [ -n "$STARTUP_CMD" ]; then
    echo "  Running startup command..."
    eval $STARTUP_CMD
    echo "  ✅ Auto-start configured!"
else
    # If already configured, pm2 startup won't output a sudo command
    pm2 startup 2>/dev/null || true
    echo "  ✅ Auto-start already configured"
fi

# Save again after startup setup
pm2 save --force

# ==========================================
# Done!
# ==========================================
echo ""
echo "======================================"
echo "  ✅ Setup Complete!                  "
echo "======================================"
echo ""
echo "  Status:     pm2 status"
echo "  Logs:       pm2 logs sys-logger-client"
echo "  Monitor:    pm2 monit"
echo "  Stop:       pm2 stop sys-logger-client"
echo "  Uninstall:  pm2 delete sys-logger-client"
echo ""
echo "  The client will auto-start on every system boot."
echo ""
