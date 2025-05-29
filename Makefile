# DevOps Researcher - Makefile

.PHONY: help install install-dev test lint format clean run analyze contribute outreach docker docker-run docs

# Default target
help: ## Show this help message
	@echo "DevOps Researcher - Available commands:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	pip install -r requirements.txt
	python -m src.setup_directories

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pre-commit
	pre-commit install
	python -m src.setup_directories

# Testing
test: ## Run all tests
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-watch: ## Run tests in watch mode
	pytest-watch -- tests/ -v

# Code Quality
lint: ## Run linting
	flake8 src/ scripts/ tests/
	mypy src/ scripts/

format: ## Format code
	black src/ scripts/ tests/
	isort src/ scripts/ tests/

format-check: ## Check code formatting
	black --check src/ scripts/ tests/
	isort --check-only src/ scripts/ tests/

# Cleaning
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

clean-output: ## Clean output files
	rm -rf output/reports/*
	rm -rf output/contributions/*
	rm -rf output/logs/*

# Main Operations
run: ## Run full analysis pipeline
	python scripts/main.py

analyze: ## Analyze companies and repositories
	python scripts/analyze_companies.py

contribute: ## Generate contributions for selected repos
	python scripts/generate_contributions.py

outreach: ## Send outreach messages
	python scripts/send_outreach.py

# Development
dev-setup: install-dev ## Set up development environment
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

dev-run: ## Run in development mode
	DEBUG=true python scripts/main.py

# Docker
docker-build: ## Build Docker image
	docker build -t devops-researcher .

docker-run: ## Run in Docker container
	docker run -it --env-file .env -v $(PWD)/output:/app/output devops-researcher

docker-dev: ## Run development environment in Docker
	docker-compose up -d

# Documentation
docs: ## Generate documentation
	cd docs && make html

docs-serve: ## Serve documentation locally
	cd docs/_build/html && python -m http.server 8080

# Database
db-init: ## Initialize database
	python -c "from src.database import init_db; init_db()"

db-migrate: ## Run database migrations
	alembic upgrade head

db-reset: ## Reset database
	rm -f devops_researcher.db
	python -c "from src.database import init_db; init_db()"

# Reports
report-companies: ## Generate companies analysis report
	python scripts/analyze_companies.py --report-only

report-contributions: ## Generate contributions report
	python scripts/generate_contributions.py --report-only

# Utilities
validate-config: ## Validate configuration
	python -c "from config.settings import Settings; print('Config is valid')"

check-tokens: ## Check API tokens validity
	python -c "from src.github_client import GitHubClient; GitHubClient().test_connection()"

setup-dirs: ## Create necessary directories
	mkdir -p output/reports output/contributions output/logs
	mkdir -p .cache

# CI/CD
ci-test: format-check lint test ## Run CI pipeline

pre-commit: format lint test ## Run pre-commit checks

# Monitoring
logs: ## Show recent logs
	tail -f output/logs/app.log

logs-errors: ## Show error logs only
	grep ERROR output/logs/app.log | tail -20

# Backup
backup: ## Backup configuration and data
	tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz config/ output/ .env

# Examples
example-analyze: ## Run analysis on sample companies
	python scripts/analyze_companies.py --companies zalando,sap --max-repos 5

example-contribute: ## Generate sample contributions
	python scripts/generate_contributions.py --org zalando --repo team-api --dry-run

example-outreach: ## Show sample outreach message
	python scripts/send_outreach.py --template email --company zalando --dry-run

# Help for specific topics
help-setup: ## Show setup instructions
	@echo "Setup Instructions:"
	@echo "1. Run 'make install-dev' to install dependencies"
	@echo "2. Copy .env.example to .env and configure"
	@echo "3. Run 'make validate-config' to check configuration"
	@echo "4. Run 'make example-analyze' to test the system"

help-github: ## Show GitHub token setup instructions
	@echo "GitHub Token Setup:"
	@echo "1. Go to https://github.com/settings/tokens"
	@echo "2. Create new token with 'public_repo' scope"
	@echo "3. Add to .env file: GITHUB_TOKEN=your_token_here"
	@echo "4. Run 'make check-tokens' to verify"