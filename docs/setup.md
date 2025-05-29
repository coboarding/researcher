# DevOps Researcher - Setup Guide

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.8+** (recommended: Python 3.11)
- **Git** for version control
- **GitHub Account** with API token
- **Internet connection** for API access

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/devops-researcher.git
cd devops-researcher

# Install dependencies
make install

# Set up development environment (optional)
make install-dev
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration file
nano .env  # or your preferred editor
```

**Required settings in `.env`:**
```bash
# Essential
GITHUB_TOKEN=your_github_token_here

# Optional but recommended
EMAIL_ADDRESS=your.email@example.com
EMAIL_FROM_NAME=Your Name
```

### 4. Get GitHub Token

1. Go to [GitHub Settings → Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes:
   - ✅ `public_repo` (access public repositories)
   - ✅ `read:org` (read organization data)
4. Copy the token and add to `.env` file

### 5. Test Installation

```bash
# Validate configuration
make validate-config

# Test GitHub connection
make check-tokens

# Run basic test
make test

# Try example analysis
make example-analyze
```

## 📋 Detailed Setup

### Python Environment Setup

#### Option A: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv devops-researcher-env

# Activate (Linux/Mac)
source devops-researcher-env/bin/activate

# Activate (Windows)
devops-researcher-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Option B: Using Conda

```bash
# Create conda environment
conda create -n devops-researcher python=3.11

# Activate environment
conda activate devops-researcher

# Install dependencies
pip install -r requirements.txt
```

#### Option C: Using Poetry

```bash
# Install poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate shell
poetry shell
```

### Directory Structure Setup

The tool will automatically create necessary directories, but you can set them up manually:

```bash
# Create output directories
mkdir -p output/reports
mkdir -p output/contributions
mkdir -p output/logs
mkdir -p .cache

# Or use make command
make setup-dirs
```

### Advanced Configuration

#### Database Setup (Optional)

For persistent storage of analysis results:

```bash
# SQLite (default - no setup needed)
DATABASE_URL=sqlite:///devops_researcher.db

# PostgreSQL (requires setup)
DATABASE_URL=postgresql://user:password@localhost:5432/devops_researcher

# Initialize database
make db-init
```

#### Email Configuration (Optional)

For automated outreach:

```bash
# Gmail setup
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_app_password  # Use App Password, not regular password

# Outlook setup
SMTP_SERVER=smtp.outlook.com
SMTP_PORT=587
EMAIL_ADDRESS=your.email@outlook.com
EMAIL_PASSWORD=your_password
```

#### LinkedIn Integration (Optional)

For LinkedIn outreach automation:

```bash
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback
```

## 🔧 Configuration Reference

### Core Settings

| Setting | Description | Default | Required |
|---------|-------------|---------|----------|
| `GITHUB_TOKEN` | GitHub API token | - | ✅ |
| `GITHUB_API_URL` | GitHub API endpoint | `https://api.github.com` | No |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |
| `DEBUG` | Debug mode | `false` | No |

### Analysis Settings

| Setting | Description | Default | Required |
|---------|-------------|---------|----------|
| `MAX_REPOS_PER_ORG` | Max repos to analyze per company | `10` | No |
| `MAX_ORGS_TO_ANALYZE` | Max organizations to process | `50` | No |
| `ANALYSIS_DELAY_SECONDS` | Delay between API calls | `1.0` | No |
| `CACHE_ENABLED` | Enable API response caching | `true` | No |
| `CACHE_DURATION_HOURS` | Cache validity period | `24` | No |

### Output Settings

| Setting | Description | Default | Required |
|---------|-------------|---------|----------|
| `OUTPUT_DIR` | Base output directory | `output` | No |
| `REPORTS_DIR` | Reports directory | `output/reports` | No |
| `CONTRIBUTIONS_DIR` | Contributions directory | `output/contributions` | No |
| `LOGS_DIR` | Logs directory | `output/logs` | No |

## 🧪 Testing Your Setup

### Basic Functionality Test

```bash
# Test imports
python -c "from src import GitHubClient; print('✅ Imports working')"

# Test configuration
python -c "from config.settings import settings; print('✅ Config loaded')"

# Test GitHub connection
python -c "from src import GitHubClient; client = GitHubClient(); print('✅ Connected' if client.test_connection() else '❌ Connection failed')"
```

### Run Example Analysis

```bash
# Quick test with a single repository
python scripts/analyze_companies.py single zalando --max-repos 1

# Test contribution generation
python scripts/generate_contributions.py single zalando team-api --dry-run

# Generate sample report
python scripts/main.py --companies zalando --max-repos 2
```

## 🛠️ Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'src'"

**Solution:**
```bash
# Make sure you're in the project root directory
pwd  # Should show .../devops-researcher

# Add current directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use the scripts with proper path
python -m scripts.main --help
```

#### "GitHub API rate limit exceeded"

**Solutions:**
1. **Add GitHub token** to `.env` file (increases limit from 60 to 5000 requests/hour)
2. **Enable caching** to reduce API calls:
   ```bash
   CACHE_ENABLED=true
   CACHE_DURATION_HOURS=24
   ```
3. **Increase delay** between requests:
   ```bash
   ANALYSIS_DELAY_SECONDS=2.0
   ```

#### "Permission denied" errors

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/*.py

# Or run with python explicitly
python scripts/main.py --help
```

#### "SSL Certificate verification failed"

**Solution:**
```bash
# Upgrade certificates (Mac)
/Applications/Python\ 3.x/Install\ Certificates.command

# Set environment variable (temporary fix)
export PYTHONHTTPSVERIFY=0

# Update pip and certificates
pip install --upgrade certifi
```

### Performance Optimization

#### For Large-Scale Analysis

```bash
# Increase cache duration
CACHE_DURATION_HOURS=72

# Use multiple workers (if implementing parallel processing)
MAX_WORKERS=4

# Reduce analysis scope
MAX_REPOS_PER_ORG=5
MAX_ORGS_TO_ANALYZE=20
```

#### For Memory Optimization

```bash
# Reduce batch sizes
BATCH_SIZE=10

# Clear cache regularly
make clean

# Use CSV output instead of HTML for large datasets
python scripts/main.py --output-format csv
```

## 🔐 Security Best Practices

### Token Security

1. **Never commit tokens** to version control
2. **Use environment variables** for sensitive data
3. **Rotate tokens regularly** (every 90 days)
4. **Use minimal required scopes** for GitHub tokens

### Environment Protection

```bash
# Add .env to .gitignore (already included)
echo ".env" >> .gitignore

# Set restrictive permissions
chmod 600 .env

# Use different tokens for different environments
cp .env .env.production
cp .env .env.development
```

## 📊 Monitoring & Logging

### Log Configuration

```bash
# Set appropriate log level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Monitor logs in real-time
tail -f output/logs/app.log

# View error logs only
grep ERROR output/logs/app.log
```

### Performance Monitoring

```bash
# Check API rate limits
python -c "from src import GitHubClient; client = GitHubClient(); print(client.get_rate_limit_status())"

# Monitor cache usage
python -c "from src import GitHubClient; client = GitHubClient(); print(client.get_cache_stats())"
```

## 🚀 Ready to Go!

Once setup is complete, you can start analyzing companies:

```bash
# Full analysis of all German companies
python scripts/main.py --full

# Analyze specific companies
python scripts/main.py --companies zalando sap trivago

# Generate contributions for best opportunities
python scripts/generate_contributions.py batch --repos zalando/team-api sap/ui5-webcomponents

# Create detailed company reports
python scripts/analyze_companies.py compare zalando sap trivago
```

## 📚 Next Steps

- Read the [Usage Guide](usage.md) for detailed examples
- Check the [API Documentation](api.md) for advanced usage
- See [Contributing Guidelines](../CONTRIBUTING.md) to improve the tool
- Join the community discussions for tips and tricks

## 🆘 Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact the maintainers for urgent issues

---

**Happy analyzing! 🎯**