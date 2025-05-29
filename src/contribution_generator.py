"""
Contribution Generator for DevOps Researcher
Automatically generates improvements for repositories (README, Makefile, tests, CI/CD).
"""
import os
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
import textwrap

from src.repo_analyzer import AnalysisResult
from config.settings import CONTRIBUTION_CONFIG, settings

logger = logging.getLogger(__name__)


@dataclass
class ContributionItem:
    """Represents a single contribution/improvement"""
    file_path: str
    content: str
    description: str
    priority: int  # 1=high, 2=medium, 3=low
    estimated_impact: str  # "high", "medium", "low"


@dataclass
class ContributionPlan:
    """Complete contribution plan for a repository"""
    repo_name: str
    owner: str
    items: List[ContributionItem]
    summary: str
    estimated_time: str  # e.g., "2-4 hours"
    created_at: datetime


class ContributionGenerator:
    """
    Generates specific improvements for repositories based on analysis results
    """

    def __init__(self):
        self.config = CONTRIBUTION_CONFIG
        self.output_dir = Path(settings.contributions_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_contributions(self, analysis: AnalysisResult) -> ContributionPlan:
        """
        Generate a complete contribution plan based on analysis results
        """
        logger.info(f"Generating contributions for {analysis.owner}/{analysis.repo_name}")

        items = []

        # Generate README improvements
        if not analysis.has_readme or analysis.readme_issues:
            readme_item = self._generate_readme_improvement(analysis)
            if readme_item:
                items.append(readme_item)

        # Generate Makefile
        if not analysis.has_makefile or analysis.makefile_issues:
            makefile_item = self._generate_makefile(analysis)
            if makefile_item:
                items.append(makefile_item)

        # Generate testing setup
        if not analysis.has_tests or analysis.testing_issues:
            test_items = self._generate_testing_setup(analysis)
            items.extend(test_items)

        # Generate CI/CD setup
        if not analysis.has_ci_cd:
            ci_cd_item = self._generate_ci_cd_setup(analysis)
            if ci_cd_item:
                items.append(ci_cd_item)

        # Generate Docker setup
        if not analysis.has_docker:
            docker_items = self._generate_docker_setup(analysis)
            items.extend(docker_items)

        # Generate code quality improvements
        if analysis.code_quality_issues:
            quality_items = self._generate_code_quality_setup(analysis)
            items.extend(quality_items)

        # Sort items by priority
        items.sort(key=lambda x: x.priority)

        # Create contribution plan
        plan = ContributionPlan(
            repo_name=analysis.repo_name,
            owner=analysis.owner,
            items=items,
            summary=self._generate_plan_summary(items),
            estimated_time=self._estimate_time(items),
            created_at=datetime.now()
        )

        # Save to files
        self._save_contribution_plan(plan)

        logger.info(f"Generated {len(items)} contribution items for {analysis.repo_name}")
        return plan

    def _generate_readme_improvement(self, analysis: AnalysisResult) -> Optional[ContributionItem]:
        """Generate improved README.md"""
        if not analysis.has_readme:
            content = self._create_new_readme(analysis)
            description = "Create comprehensive README.md with all essential sections"
            priority = 1
        else:
            content = self._improve_existing_readme(analysis)
            description = "Improve existing README.md with missing sections and better formatting"
            priority = 2

        return ContributionItem(
            file_path="README.md",
            content=content,
            description=description,
            priority=priority,
            estimated_impact="high"
        )

    def _create_new_readme(self, analysis: AnalysisResult) -> str:
        """Create a new README from scratch"""
        repo_title = analysis.repo_name.replace('-', ' ').replace('_', ' ').title()

        readme_template = f"""# {repo_title}

{analysis.description or f"A {analysis.language or 'software'} project by {analysis.owner}"}

[![Build Status](https://github.com/{analysis.owner}/{analysis.repo_name}/workflows/CI/badge.svg)](https://github.com/{analysis.owner}/{analysis.repo_name}/actions)
[![License](https://img.shields.io/github/license/{analysis.owner}/{analysis.repo_name})](LICENSE)
[![Contributors](https://img.shields.io/github/contributors/{analysis.owner}/{analysis.repo_name})](https://github.com/{analysis.owner}/{analysis.repo_name}/graphs/contributors)

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

- ⚡ Fast and efficient
- 🔧 Easy to configure
- 📚 Well documented
- 🧪 Thoroughly tested

## Installation

### Prerequisites

- {analysis.language or 'Your runtime'} (version X.X or higher)
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/{analysis.owner}/{analysis.repo_name}.git
cd {analysis.repo_name}

# Install dependencies
make install

# Run the project
make run
```

### Manual Installation

```bash
# Install dependencies manually
# Add your specific installation steps here
```

## Usage

### Basic Usage

```{analysis.language.lower() if analysis.language else 'bash'}
# Add basic usage examples here
```

### Advanced Usage

```{analysis.language.lower() if analysis.language else 'bash'}
# Add advanced usage examples here
```

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/{analysis.owner}/{analysis.repo_name}.git
cd {analysis.repo_name}

# Install development dependencies
make install-dev

# Run tests
make test

# Run linting
make lint
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
# Add language-specific test commands
```

### Code Quality

This project uses automated code quality tools:

- **Linting**: Ensures code follows style guidelines
- **Formatting**: Automatically formats code
- **Testing**: Comprehensive test suite

```bash
# Check code quality
make lint

# Format code
make format

# Run all quality checks
make check
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`make test`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Workflow

```bash
# Start development
make dev-setup

# Make changes and test
make test

# Submit changes
git add .
git commit -m "Your descriptive commit message"
git push origin your-feature-branch
```

## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/{analysis.owner}/{analysis.repo_name}/issues)
- 💬 [Discussions](https://github.com/{analysis.owner}/{analysis.repo_name}/discussions)

## Acknowledgments

- Thanks to all [contributors](https://github.com/{analysis.owner}/{analysis.repo_name}/graphs/contributors)
- Built with ❤️ by the {analysis.owner} team

---

**Note**: This README was generated to help improve project documentation. Please customize it according to your specific project needs.
"""
        return readme_template

    def _improve_existing_readme(self, analysis: AnalysisResult) -> str:
        """Generate improvements for existing README"""
        improvements = []

        if "installation" not in [issue.lower() for issue in analysis.readme_issues]:
            improvements.append("""
## Installation

```bash
# Clone the repository
git clone https://github.com/{}/{}.git
cd {}

# Install dependencies
make install
```
""".format(analysis.owner, analysis.repo_name, analysis.repo_name))

        if "usage" not in [issue.lower() for issue in analysis.readme_issues]:
            improvements.append(f"""
## Usage

### Basic Usage

```{analysis.language.lower() if analysis.language else 'bash'}
# Add your usage examples here
```
""")

        if "badges" in str(analysis.readme_issues):
            improvements.append(f"""
<!-- Add these badges to the top of your README -->
[![Build Status](https://github.com/{analysis.owner}/{analysis.repo_name}/workflows/CI/badge.svg)](https://github.com/{analysis.owner}/{analysis.repo_name}/actions)
[![License](https://img.shields.io/github/license/{analysis.owner}/{analysis.repo_name})](LICENSE)
[![Contributors](https://img.shields.io/github/contributors/{analysis.owner}/{analysis.repo_name})](https://github.com/{analysis.owner}/{analysis.repo_name}/graphs/contributors)
""")

        return "\n".join(improvements)

    def _generate_makefile(self, analysis: AnalysisResult) -> ContributionItem:
        """Generate a comprehensive Makefile"""

        # Detect language-specific commands
        if analysis.language:
            lang_commands = self._get_language_commands(analysis.language)
        else:
            lang_commands = self._get_generic_commands()

        makefile_content = f"""# Makefile for {analysis.repo_name}
# Generated by DevOps Researcher

.PHONY: help install install-dev test lint format clean build run docker docker-run

# Default target
help: ## Show this help message
\t@echo "Available commands:"
\t@echo
\t@grep -E '^[a-zA-Z_-]+:.*?## .*$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {{FS = ":.*?## "}}; {{printf "  \\033[36m%-20s\\033[0m %s\\n", $1, $2}}'

# Installation
install: ## Install production dependencies
{lang_commands['install']}

install-dev: ## Install development dependencies
{lang_commands['install_dev']}

# Testing
test: ## Run tests
{lang_commands['test']}

test-coverage: ## Run tests with coverage
{lang_commands['test_coverage']}

test-watch: ## Run tests in watch mode
{lang_commands['test_watch']}

# Code Quality
lint: ## Run linting
{lang_commands['lint']}

format: ## Format code
{lang_commands['format']}

format-check: ## Check code formatting
{lang_commands['format_check']}

# Build
build: ## Build the project
{lang_commands['build']}

clean: ## Clean build artifacts
{lang_commands['clean']}

# Development
dev: ## Start development server
{lang_commands['dev']}

run: ## Run the application
{lang_commands['run']}

# Docker
docker-build: ## Build Docker image
\tdocker build -t {analysis.repo_name.lower()} .

docker-run: ## Run Docker container
\tdocker run -it --rm {analysis.repo_name.lower()}

docker-dev: ## Run development environment with Docker
\tdocker-compose up -d

# Documentation
docs: ## Generate documentation
{lang_commands['docs']}

docs-serve: ## Serve documentation locally
{lang_commands['docs_serve']}

# Utilities
setup: install-dev ## Setup development environment
\t@echo "Development environment setup complete"

check: lint test ## Run all checks
\t@echo "All checks passed"

pre-commit: format lint test ## Run pre-commit checks
\t@echo "Pre-commit checks completed"

# Release
version: ## Show current version
\t@echo "Version: $(shell git describe --tags --always --dirty)"

tag: ## Create a new tag
\t@read -p "Enter tag name: " tag; git tag -a $tag -m "Release $tag"

# Help
list: ## List all available targets
\t@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {{if ($1 !~ "^[#.]") print $1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$'
"""

        return ContributionItem(
            file_path="Makefile",
            content=makefile_content,
            description="Add comprehensive Makefile with common development targets",
            priority=1,
            estimated_impact="high"
        )

    def _get_language_commands(self, language: str) -> Dict[str, str]:
        """Get language-specific commands for Makefile"""
        language = language.lower()

        if language == "python":
            return {
                'install': '\tpip install -r requirements.txt',
                'install_dev': '\tpip install -r requirements-dev.txt\n\tpre-commit install',
                'test': '\tpytest',
                'test_coverage': '\tpytest --cov=src --cov-report=html',
                'test_watch': '\tpytest-watch',
                'lint': '\tflake8 src/ tests/\n\tmypy src/',
                'format': '\tblack src/ tests/\n\tisort src/ tests/',
                'format_check': '\tblack --check src/ tests/\n\tisort --check-only src/ tests/',
                'build': '\tpython setup.py sdist bdist_wheel',
                'clean': '\tfind . -type f -name "*.pyc" -delete\n\tfind . -type d -name "__pycache__" -delete\n\trm -rf build/ dist/ *.egg-info/',
                'dev': '\tpython -m src.main --dev',
                'run': '\tpython -m src.main',
                'docs': '\tsphinx-build -b html docs/ docs/_build/html',
                'docs_serve': '\tcd docs/_build/html && python -m http.server 8080'
            }
        elif language == "javascript" or language == "typescript":
            return {
                'install': '\tnpm install',
                'install_dev': '\tnpm install\n\tnpm run prepare',
                'test': '\tnpm test',
                'test_coverage': '\tnpm run test:coverage',
                'test_watch': '\tnpm run test:watch',
                'lint': '\tnpm run lint',
                'format': '\tnpm run format',
                'format_check': '\tnpm run format:check',
                'build': '\tnpm run build',
                'clean': '\trm -rf node_modules/ dist/ build/',
                'dev': '\tnpm run dev',
                'run': '\tnpm start',
                'docs': '\tnpm run docs',
                'docs_serve': '\tnpm run docs:serve'
            }
        elif language == "go":
            return {
                'install': '\tgo mod download',
                'install_dev': '\tgo mod download\n\tgo install github.com/golangci/golangci-lint/cmd/golangci-lint@latest',
                'test': '\tgo test ./...',
                'test_coverage': '\tgo test -coverprofile=coverage.out ./...\n\tgo tool cover -html=coverage.out -o coverage.html',
                'test_watch': '\tgotestsum --watch',
                'lint': '\tgolangci-lint run',
                'format': '\tgo fmt ./...',
                'format_check': '\ttest -z $(go fmt ./...)',
                'build': '\tgo build -o bin/app ./cmd/main.go',
                'clean': '\tgo clean\n\trm -rf bin/',
                'dev': '\tgo run ./cmd/main.go --dev',
                'run': '\tgo run ./cmd/main.go',
                'docs': '\tgodoc -http=:6060',
                'docs_serve': '\techo "Documentation available at http://localhost:6060"'
            }
        else:
            return self._get_generic_commands()

    def _get_generic_commands(self) -> Dict[str, str]:
        """Get generic commands for unknown languages"""
        return {
            'install': '\t# Add installation commands here',
            'install_dev': '\t# Add development installation commands here',
            'test': '\t# Add test commands here',
            'test_coverage': '\t# Add test coverage commands here',
            'test_watch': '\t# Add test watch commands here',
            'lint': '\t# Add linting commands here',
            'format': '\t# Add formatting commands here',
            'format_check': '\t# Add format checking commands here',
            'build': '\t# Add build commands here',
            'clean': '\t# Add cleanup commands here',
            'dev': '\t# Add development server commands here',
            'run': '\t# Add run commands here',
            'docs': '\t# Add documentation generation commands here',
            'docs_serve': '\t# Add documentation serving commands here'
        }

    def _generate_testing_setup(self, analysis: AnalysisResult) -> List[ContributionItem]:
        """Generate testing configuration files"""
        items = []

        if analysis.language and analysis.language.lower() == "python":
            # pytest.ini
            pytest_config = """[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    external: Tests that require external services
"""

            items.append(ContributionItem(
                file_path="pytest.ini",
                content=pytest_config,
                description="Add pytest configuration for better testing",
                priority=2,
                estimated_impact="medium"
            ))

            # Basic test file
            test_content = f"""\"\"\"
Basic tests for {analysis.repo_name}
\"\"\"
import pytest


class TestBasic:
    \"\"\"Basic test class\"\"\"
    
    def test_import(self):
        \"\"\"Test that the main module can be imported\"\"\"
        # Add your import test here
        assert True
    
    def test_basic_functionality(self):
        \"\"\"Test basic functionality\"\"\"
        # Add your basic functionality test here
        assert True


@pytest.mark.unit
def test_example():
    \"\"\"Example unit test\"\"\"
    assert 1 + 1 == 2


@pytest.mark.integration
def test_integration_example():
    \"\"\"Example integration test\"\"\"
    # Add integration test here
    assert True
"""

            items.append(ContributionItem(
                file_path="tests/test_basic.py",
                content=test_content,
                description="Add basic test structure and example tests",
                priority=2,
                estimated_impact="medium"
            ))

        return items

    def _generate_ci_cd_setup(self, analysis: AnalysisResult) -> ContributionItem:
        """Generate GitHub Actions workflow"""

        if analysis.language and analysis.language.lower() == "python":
            workflow = self._generate_python_workflow(analysis)
        elif analysis.language and analysis.language.lower() in ["javascript", "typescript"]:
            workflow = self._generate_node_workflow(analysis)
        elif analysis.language and analysis.language.lower() == "go":
            workflow = self._generate_go_workflow(analysis)
        else:
            workflow = self._generate_generic_workflow(analysis)

        return ContributionItem(
            file_path=".github/workflows/ci.yml",
            content=workflow,
            description="Add CI/CD pipeline with GitHub Actions",
            priority=1,
            estimated_impact="high"
        )

    def _generate_python_workflow(self, analysis: AnalysisResult) -> str:
        """Generate Python-specific GitHub Actions workflow"""
        return f"""name: CI

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v4
      with:
        python-version: ${{{{ matrix.python-version }}}}
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('**/requirements*.txt') }}}}
        restore-keys: |
          ${{{{ runner.os }}}}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        make install-dev
    
    - name: Lint with flake8
      run: make lint
    
    - name: Check formatting with black
      run: make format-check
    
    - name: Run tests
      run: make test-coverage
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run security checks
      run: |
        pip install safety bandit
        safety check
        bandit -r src/
"""

    def _generate_node_workflow(self, analysis: AnalysisResult) -> str:
        """Generate Node.js-specific GitHub Actions workflow"""
        return f"""name: CI

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16.x, 18.x, 20.x]

    steps:
    - uses: actions/checkout@v4
    
    - name: Use Node.js ${{{{ matrix.node-version }}}}
      uses: actions/setup-node@v4
      with:
        node-version: ${{{{ matrix.node-version }}}}
        cache: 'npm'
    
    - name: Install dependencies
      run: make install
    
    - name: Run linting
      run: make lint
    
    - name: Check formatting
      run: make format-check
    
    - name: Run tests
      run: make test-coverage
    
    - name: Build project
      run: make build
"""

    def _generate_go_workflow(self, analysis: AnalysisResult) -> str:
        """Generate Go-specific GitHub Actions workflow"""
        return f"""name: CI

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        go-version: [1.19, "1.20", "1.21"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Go ${{{{ matrix.go-version }}}}
      uses: actions/setup-go@v4
      with:
        go-version: ${{{{ matrix.go-version }}}}
    
    - name: Cache Go modules
      uses: actions/cache@v3
      with:
        path: ~/go/pkg/mod
        key: ${{{{ runner.os }}}}-go-${{{{ hashFiles('**/go.sum') }}}}
        restore-keys: |
          ${{{{ runner.os }}}}-go-
    
    - name: Install dependencies
      run: make install
    
    - name: Run linting
      run: make lint
    
    - name: Check formatting
      run: make format-check
    
    - name: Run tests
      run: make test-coverage
    
    - name: Build
      run: make build
"""

    def _generate_generic_workflow(self, analysis: AnalysisResult) -> str:
        """Generate generic GitHub Actions workflow"""
        return f"""name: CI

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4
    
    - name: Install dependencies
      run: make install
    
    - name: Run tests
      run: make test
    
    - name: Build project
      run: make build
"""

    def _generate_docker_setup(self, analysis: AnalysisResult) -> List[ContributionItem]:
        """Generate Docker configuration files"""
        items = []

        # Dockerfile
        dockerfile_content = self._generate_dockerfile(analysis)
        items.append(ContributionItem(
            file_path="Dockerfile",
            content=dockerfile_content,
            description="Add Dockerfile for containerization",
            priority=2,
            estimated_impact="medium"
        ))

        # .dockerignore
        dockerignore_content = self._generate_dockerignore(analysis)
        items.append(ContributionItem(
            file_path=".dockerignore",
            content=dockerignore_content,
            description="Add .dockerignore to optimize Docker builds",
            priority=3,
            estimated_impact="low"
        ))

        # docker-compose.yml
        compose_content = self._generate_docker_compose(analysis)
        items.append(ContributionItem(
            file_path="docker-compose.yml",
            content=compose_content,
            description="Add docker-compose for development environment",
            priority=3,
            estimated_impact="medium"
        ))

        return items

    def _generate_dockerfile(self, analysis: AnalysisResult) -> str:
        """Generate Dockerfile based on project language"""
        language = analysis.language.lower() if analysis.language else "generic"

        if language == "python":
            return f"""# Dockerfile for {analysis.repo_name}
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements*.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run application
CMD ["python", "-m", "src.main"]
"""
        elif language in ["javascript", "typescript"]:
            return f"""# Dockerfile for {analysis.repo_name}
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:3000/health || exit 1

# Run application
CMD ["npm", "start"]
"""
        else:
            return f"""# Dockerfile for {analysis.repo_name}
FROM ubuntu:22.04

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Build application
RUN make build

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Run application
CMD ["make", "run"]
"""

    def _generate_dockerignore(self, analysis: AnalysisResult) -> str:
        """Generate .dockerignore file"""
        return """# Git
.git
.gitignore
README.md

# CI/CD
.github/
.gitlab-ci.yml
.travis.yml

# Documentation
docs/
*.md
LICENSE

# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
pip-log.txt
pip-delete-this-directory.txt

# Testing
.coverage
.pytest_cache/
.tox/
.nox/
coverage.xml
*.cover
.hypothesis/
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Runtime
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Build artifacts
dist/
build/
*.egg-info/
.cache/
"""

    def _generate_docker_compose(self, analysis: AnalysisResult) -> str:
        """Generate docker-compose.yml file"""
        return f"""version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=development
    volumes:
      - .:/app
      - /app/node_modules
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: {analysis.repo_name.replace('-', '_')}
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
"""

    def _generate_code_quality_setup(self, analysis: AnalysisResult) -> List[ContributionItem]:
        """Generate code quality configuration files"""
        items = []

        if analysis.language and analysis.language.lower() == "python":
            # .pre-commit-config.yaml
            precommit_config = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.0
    hooks:
      - id: mypy
"""

            items.append(ContributionItem(
                file_path=".pre-commit-config.yaml",
                content=precommit_config,
                description="Add pre-commit hooks for code quality",
                priority=2,
                estimated_impact="medium"
            ))

        return items

    def _generate_plan_summary(self, items: List[ContributionItem]) -> str:
        """Generate a summary of the contribution plan"""
        if not items:
            return "No contributions needed - repository is already well-maintained!"

        high_priority = len([item for item in items if item.priority == 1])
        medium_priority = len([item for item in items if item.priority == 2])
        low_priority = len([item for item in items if item.priority == 3])

        summary = f"Contribution plan includes {len(items)} improvements:\n"
        if high_priority:
            summary += f"- {high_priority} high priority items (essential improvements)\n"
        if medium_priority:
            summary += f"- {medium_priority} medium priority items (recommended improvements)\n"
        if low_priority:
            summary += f"- {low_priority} low priority items (nice-to-have improvements)\n"

        return summary

    def _estimate_time(self, items: List[ContributionItem]) -> str:
        """Estimate time needed for all contributions"""
        if not items:
            return "0 hours"

        # Simple estimation based on number and priority of items
        total_hours = 0
        for item in items:
            if item.priority == 1:
                total_hours += 2  # High priority items take more time
            elif item.priority == 2:
                total_hours += 1  # Medium priority items
            else:
                total_hours += 0.5  # Low priority items

        if total_hours <= 2:
            return "1-2 hours"
        elif total_hours <= 4:
            return "2-4 hours"
        elif total_hours <= 8:
            return "4-8 hours"
        else:
            return f"{int(total_hours)}+ hours"

    def _save_contribution_plan(self, plan: ContributionPlan) -> None:
        """Save contribution plan to files"""
        repo_dir = self.output_dir / f"{plan.owner}_{plan.repo_name}"
        repo_dir.mkdir(parents=True, exist_ok=True)

        # Save each contribution item as a separate file
        for item in plan.items:
            file_path = repo_dir / item.file_path.replace('/', '_')
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w') as f:
                f.write(f"# {item.description}\n")
                f.write(f"# Priority: {item.priority} | Impact: {item.estimated_impact}\n\n")
                f.write(item.content)

        # Save plan summary
        summary_path = repo_dir / "CONTRIBUTION_PLAN.md"
        with open(summary_path, 'w') as f:
            f.write(f"# Contribution Plan: {plan.repo_name}\n\n")
            f.write(f"**Repository**: {plan.owner}/{plan.repo_name}\n")
            f.write(f"**Generated**: {plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Estimated Time**: {plan.estimated_time}\n\n")
            f.write(f"## Summary\n\n{plan.summary}\n\n")
            f.write("## Contributions\n\n")

            for i, item in enumerate(plan.items, 1):
                f.write(f"### {i}. {item.description}\n")
                f.write(f"- **File**: `{item.file_path}`\n")
                f.write(f"- **Priority**: {['High', 'Medium', 'Low'][item.priority-1] if item.priority <= 3 else 'Low'}\n")
                f.write(f"- **Estimated Impact**: {item.estimated_impact.capitalize()}\n\n")
                f.write(f"```\n{item.content}\n```\n\n")