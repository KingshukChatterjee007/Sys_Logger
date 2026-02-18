#!/bin/bash

# =====================================
# Sys_Logger Client - Linux/Mac Setup Script
# =====================================

echo "🚀 Sys_Logger Client - Linux/Mac Setup"
echo "===================================="
echo ""

# 1. Check/Install PM2
echo "📦 Step 1: Checking Environment..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js first."
    exit 1
fi

if ! command -v pm2 &> /dev/null; then
    echo "📥 Installing PM2..."
    sudo npm install -g pm2
    # Ensure local bin is in path if sudo npm install didn't put it in global bin for some users 
    # (usually sudo does put somewhat global but user install is safer generally without sudo if configured)
    # assuming standard setup
else
    echo "✅ PM2 installed"
fi

# 2. Setup Python Environment
echo "🐍 Step 2: Setting up Python..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure & Start
echo "🚀 Step 3: Starting Service..."
pm2 delete sys-logger-client 2> /dev/null
# Use the python binary from the virtual environment
pm2 start ecosystem.config.js --interpreter ./venv/bin/python

pm2 save
# Note: pm2 startup might require sudo and user interaction to copy/paste command
echo "⚠️  To enable startup on boot, run:"
pm2 startup

echo ""
echo "✅ Setup Complete! Client is running in background."
echo "To monitor: pm2 monit"
echo "To view logs: pm2 logs sys-logger-client"
