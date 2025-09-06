# Morgan - Makefile for easy development and testing

.PHONY: help install test test-models clean run config lint format

# Default target
help:
	@echo "🤖 Morgan - Available commands:"
	@echo ""
	@echo "📦 Setup:"
	@echo "  make install     - Install dependencies (Poetry or pip)"
	@echo "  make config      - Check configuration"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test        - Run all tests"
	@echo "  make test-models - Test data models only"
	@echo ""
	@echo "🚀 Running:"
	@echo "  make run         - Run Morgan analysis"
	@echo "  make run-demo    - Run demo with limited scope"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make lint        - Run linting"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean temporary files"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	@if command -v poetry >/dev/null 2>&1; then \
		echo "Using Poetry..."; \
		poetry install; \
	else \
		echo "Using pip..."; \
		pip3 install -r requirements.txt; \
	fi
	@echo "✅ Dependencies installed!"

# Check configuration
config:
	@echo "⚙️ Checking Morgan configuration..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry run python main.py config; \
	else \
		python3 main.py config; \
	fi

# Test data models
test-models:
	@echo "🧪 Testing data models..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry run python models.py; \
	else \
		python3 models.py; \
	fi

# Test priority engine
test-priority:
	@echo "🧪 Testing priority engine..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry run python priority_engine.py; \
	else \
		python3 priority_engine.py; \
	fi

# Run all basic tests
test: test-models test-priority
	@echo "✅ All tests completed!"

# Run Morgan analysis
run:
	@echo "🚀 Running Morgan analysis..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry run python main.py analyze; \
	else \
		python3 main.py analyze; \
	fi

# Run demo with limited scope
run-demo:
	@echo "🚀 Running Morgan demo (limited scope)..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry run python main.py analyze --hours 1 --max 10; \
	else \
		python3 main.py analyze --hours 1 --max 10; \
	fi

# Show detailed todo
details:
	@echo "📖 Showing todo details..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry run python main.py details 1; \
	else \
		python3 main.py details 1; \
	fi

# Show stats
stats:
	@echo "📊 Showing usage stats..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry run python main.py stats; \
	else \
		python3 main.py stats; \
	fi

# Linting
lint:
	@echo "🔍 Running linting..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry run ruff check .; \
	else \
		if command -v ruff >/dev/null 2>&1; then \
			ruff check .; \
		else \
			echo "Ruff not installed, skipping..."; \
		fi; \
	fi

# Format code
format:
	@echo "🎨 Formatting code..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry run black .; \
	else \
		if command -v black >/dev/null 2>&1; then \
			black .; \
		else \
			echo "Black not installed, skipping..."; \
		fi; \
	fi

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -f *.log
	@echo "✅ Cleanup completed!"

# Development shortcuts
dev-setup: install
	@echo "🛠️ Setting up development environment..."
	@cp .env.example .env 2>/dev/null || echo ".env.example not found, please create .env manually"
	@echo "✅ Development setup complete!"
	@echo "💡 Don't forget to edit .env with your API keys!"

# Quick start for new users
quick-start: dev-setup config
	@echo "🚀 Quick start completed!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env file with your API keys"
	@echo "2. Run: make test"
	@echo "3. Run: make run-demo"