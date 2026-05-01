.PHONY: help setup generate publish test clean

help:
	@echo "Azure AI LinkedIn Agent - Commands"
	@echo "================================="
	@echo "make setup      - Install all dependencies"
	@echo "make generate   - Generate a new post"
	@echo "make publish    - Publish latest post to LinkedIn"
	@echo "make test       - Run test suite"
	@echo "make clean      - Clean generated files"

setup:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "🎭 Installing Playwright browsers..."
	playwright install chromium
	@echo "✅ Setup complete!"

generate:
	@echo "🤖 Generating LinkedIn post..."
	python main.py --model template

publish:
	@echo "📤 Publishing to LinkedIn..."
	python publish.py

login:
	@echo "🔐 Authenticating with LinkedIn..."
	python publish.py --login-only

dry-run:
	@echo "🔍 Testing publish (dry run)..."
	python publish.py --dry-run

list:
	@echo "📚 Listing all posts..."
	python publish.py --list

clean:
	@echo "🧹 Cleaning generated files..."
	rm -f data/ready_to_post.txt
	rm -f data/latest_news.json
	rm -f data/agent_*.log
	rm -f data/linkedin_session.json
	rm -rf data/screenshots/
	@echo "✅ Cleaned!"