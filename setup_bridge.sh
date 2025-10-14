#!/bin/bash
# setup_bridge.sh
# Auto-installs and runs the Baileys Bridge service

set -e  # Exit on any error

echo "🚀 Setting up Baileys Bridge environment..."

# Move into bridge directory
cd "$(dirname "$0")/app/baileys_bridge"

# Ensure Node.js & npm exist
if ! command -v node &>/dev/null; then
  echo "❌ Node.js not found. Please install Node 18+ first."
  exit 1
fi

if ! command -v npm &>/dev/null; then
  echo "❌ npm not found. Please install npm."
  exit 1
fi

# Check and install dependencies (locally for the app)
echo "📦 Installing npm dependencies..."
npm install express @whiskeysockets/baileys pino --save

# Check if PM2 is installed globally
if ! command -v pm2 &>/dev/null; then
  echo "🔧 PM2 not found. Installing globally..."
  sudo npm install -g pm2
else
  echo "✅ PM2 is already installed."
fi

# Start the bridge using PM2
echo "🟢 Starting Baileys Bridge service with PM2..."
pm2 delete baileys_bridge >/dev/null 2>&1 || true
pm2 start baileys_bridge.js --name baileys_bridge

# Save PM2 process list and enable startup on boot
pm2 save
pm2 startup -u $USER --hp $HOME | tail -n 1 | bash || true

echo ""
echo "✅ Baileys Bridge is up and running!"
echo "🌍 Accessible at: http://localhost:3000"
echo "🧩 Check status with: pm2 status"
echo "📜 View logs with: pm2 logs baileys_bridge"
