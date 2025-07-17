#!/bin/bash

# Setup script for MCP browser tools
echo "Setting up MCP Browser Tools..."
echo "=" * 50

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Check if python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8+."
    exit 1
fi

# Install MCP browser server options
echo "Installing MCP browser servers..."

# Option 1: Browser-use MCP server (recommended)
echo "Installing browser-use MCP server..."
npm install -g @co-browser/browser-use-mcp

# Option 2: Puppeteer MCP server (fallback)
echo "Installing Puppeteer MCP server..."
npm install -g @modelcontextprotocol/server-puppeteer

# Option 3: Playwright MCP server (alternative)
echo "Installing Playwright server dependencies..."
npm install -g playwright
npx playwright install

# Install Python MCP client
echo "Installing Python MCP client..."
pip install mcp

# Optional: Install browser dependencies
echo "Installing browser dependencies..."
pip install playwright aiohttp

echo ""
echo "Setup completed!"
echo "Available MCP browser servers:"
echo "  - @co-browser/browser-use-mcp (recommended)"
echo "  - @modelcontextprotocol/server-puppeteer"
echo "  - Local playwright server"
echo ""
echo "To use MCP browser tools:"
echo "1. Copy .env.example to .env"
echo "2. Set ENABLE_MCP=true in .env"
echo "3. Configure MCP_BROWSER_* settings"
echo "4. Run: python examples/browser_mcp_example.py"