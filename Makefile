.PHONY: help test test-claude test-codex test-gemini test-all test-quick clean install

help:
	@echo "Agent Sandbox Test Targets:"
	@echo "  make install      - Install development dependencies"
	@echo "  make test         - Run tests (default: claude agent)"
	@echo "  make test-claude  - Run Claude agent tests"
	@echo "  make test-codex   - Run Codex agent tests"
	@echo "  make test-gemini  - Run Gemini agent tests"
	@echo "  make test-all     - Run tests for all agents"
	@echo "  make test-quick   - Quick tests (skip slow tests)"
	@echo "  make clean        - Clean test files"

install:
	pip install -e ".[test]"

test:
	pytest tests/ -v

test-claude:
	pytest tests/ --agent=claude -v

test-codex:
	pytest tests/ --agent=codex -v

test-gemini:
	pytest tests/ --agent=gemini -v

test-all:
	@echo "=== Testing Claude ==="
	pytest tests/ --agent=claude -v || true
	@echo "\n=== Testing Codex ==="
	pytest tests/ --agent=codex -v || true
	@echo "\n=== Testing Gemini ==="
	pytest tests/ --agent=gemini -v || true

test-quick:
	pytest tests/ -v -m "not slow"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
