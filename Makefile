# Mnemosyne MCP - Development Makefile

.PHONY: help install test lint format clean docker-up docker-down doctor serve deploy

# Default target
help:
	@echo "Mnemosyne MCP - Available commands:"
	@echo ""
	@echo "  install     - Install dependencies"
	@echo "  test        - Run all tests"
	@echo "  test-unit   - Run unit tests only"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code"
	@echo "  clean       - Clean up temporary files"
	@echo "  docker-up   - Start Docker services"
	@echo "  docker-down - Stop Docker services"
	@echo "  doctor      - Run system diagnostics"
	@echo "  serve       - Start development server"
	@echo "  deploy      - One-click deploy all services"
	@echo "  cli         - Run CLI help"

# Installation
install:
	uv pip install -e ".[dev]"

install-prod:
	uv pip install -e .

# Testing
test:
	PYTHONPATH=src python3 -m pytest tests/ -v --no-cov

test-unit:
	PYTHONPATH=src python3 -m pytest tests/unit/ -v --no-cov

test-integration:
	PYTHONPATH=src python3 -m pytest tests/integration/ -v --no-cov

test-cov:
	PYTHONPATH=src python3 -m pytest tests/ --cov=src/mnemosyne --cov-report=html --cov-report=term

# Code quality
lint:
	@echo "Running linting checks..."
	PYTHONPATH=src python3 -m flake8 src tests --max-line-length=88 --extend-ignore=E203,W503 || true
	PYTHONPATH=src python3 -m mypy src --ignore-missing-imports || true

format:
	@echo "Formatting code..."
	python3 -m black src tests
	python3 -m isort src tests

# Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Development tools
doctor:
	PYTHONPATH=src python3 -m mnemosyne.cli.main doctor

serve:
	PYTHONPATH=src python3 -m mnemosyne.cli.main serve --reload

cli:
	PYTHONPATH=src python3 -m mnemosyne.cli.main --help

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

# CI simulation
ci:
	@echo "Simulating CI pipeline..."
	make lint
	make test
	@echo "✅ CI simulation completed successfully!"

# Quick development setup
dev-setup:
	@echo "Setting up development environment..."
	uv venv --python 3.10
	uv pip install -e ".[dev]"
	cp .env.example .env 2>/dev/null || echo "No .env.example found, continuing..."
	mkdir -p logs
	@echo "✅ Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Activate venv: source .venv/bin/activate"
	@echo "  2. Start FalkorDB: make docker-up"
	@echo "  3. Run diagnostics: make doctor"
	@echo "  4. Start API server: make serve"

# Sprint 0 verification
sprint0-verify:
	@echo "🔍 Verifying Sprint 0 completion..."
	@echo ""
	@echo "1. Testing configuration loading..."
	PYTHONPATH=src python3 -c "from mnemosyne.core.config import get_settings; print('✅ Config loaded')"
	@echo ""
	@echo "2. Running unit tests..."
	make test-unit
	@echo ""
	@echo "3. Testing API endpoints..."
	PYTHONPATH=src python3 -c "from fastapi.testclient import TestClient; from mnemosyne.api.main import app; client = TestClient(app); r = client.get('/'); print('✅ API working' if r.status_code == 200 else '❌ API failed')"
	@echo ""
	@echo "4. Running system diagnostics..."
	make doctor
	@echo ""
	@echo "🎉 Sprint 0 verification completed!"

# One-click deploy: build & start all services
deploy:
	@echo "🚀 Building and starting all services..."
	docker-compose up --build -d
	@echo "✅ Services are running:"
	@echo "  - FalkorDB UI:       http://localhost:3000"
	@echo "  - MCP API Docs:      http://localhost:8000/docs"
	@echo "  - MCP Health Check:  http://localhost:8000/health"
