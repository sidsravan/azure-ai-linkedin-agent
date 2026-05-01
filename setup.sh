#!/bin/bash

echo "╔══════════════════════════════════════════════════════╗"
echo "║  Azure AI LinkedIn Agent - Setup                    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright
echo "🎭 Installing Playwright browsers..."
playwright install chromium

# Create directories
echo "📁 Creating directories..."
mkdir -p data/screenshots
touch data/.gitkeep

# Setup environment file
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env with your LinkedIn credentials:"
    echo "   nano .env"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Quick Start:"
echo "  1. Edit .env with your LinkedIn credentials"
echo "  2. Generate post: python main.py"
echo "  3. Publish post: python publish.py"
echo ""
echo "Or use Makefile:"
echo "  make generate"
echo "  make publish"