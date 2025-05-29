"""
DevOps Researcher - Configuration Settings
"""
import os
from typing import List, Dict, Any
from pathlib import Path
from pydantic import validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8'
    }

    # Application Info
    app_name: str = "DevOps Researcher"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # GitHub API Configuration
    github_token: str = ""
    github_api_url: str = "https://api.github.com"
    github_rate_limit: int = 5000

    # Paths
    output_dir: str = "output"
    reports_dir: str = "output/reports"
    contributions_dir: str = "output/contributions"
    logs_dir: str = "output/logs"
    cache_dir: str = ".cache"

    # Analysis Settings
    max_repos_per_org: int = 10
    max_orgs_to_analyze: int = 50
    analysis_delay_seconds: float = 1.0
    retry_attempts: int = 3

    # Email Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_address: str = ""
    email_password: str = ""
    email_from_name: str = ""

    # LinkedIn Configuration
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/callback"

    # Database Configuration
    database_url: str = "sqlite:///devops_researcher.db"

    # Web Dashboard
    web_host: str = "localhost"
    web_port: int = 8000
    secret_key: str = "your-secret-key-change-this"

    # Notification Settings
    slack_webhook_url: str = ""
    discord_webhook_url: str = ""

    # Target Configuration
    target_countries: List[str] = ["Germany", "Austria", "Switzerland"]
    target_keywords: List[str] = ["devops", "cloud", "infrastructure", "sysadmin", "platform", "sre"]

    # Contribution Settings
    auto_create_prs: bool = False
    auto_fork_repos: bool = False
    contribution_branch_prefix: str = "feature/devops-researcher-"
    commit_message_prefix: str = "[DevOps Researcher]"

    # Rate Limiting
    requests_per_minute: int = 60
    requests_per_hour: int = 1000

    # Caching
    cache_enabled: bool = True
    cache_duration_hours: int = 24

    @validator('target_countries', pre=True)
    def parse_countries(cls, v):
        if isinstance(v, str):
            return [country.strip() for country in v.split(',')]
        return v

    @validator('target_keywords', pre=True)
    def parse_keywords(cls, v):
        if isinstance(v, str):
            return [keyword.strip() for keyword in v.split(',')]
        return v

    @validator('github_token')
    def validate_github_token(cls, v):
        if not v:
            print("Warning: GITHUB_TOKEN not set. API rate limits will be lower.")
        return v

    def create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.output_dir,
            self.reports_dir,
            self.contributions_dir,
            self.logs_dir,
            self.cache_dir
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()

# Analysis configuration
ANALYSIS_CONFIG = {
    "readme_quality_checks": {
        "min_length": 100,
        "required_sections": ["installation", "usage", "description"],
        "check_badges": True,
        "check_examples": True,
        "check_license": True
    },
    "makefile_checks": {
        "required_targets": ["install", "test", "clean"],
        "recommended_targets": ["lint", "format", "help", "build"],
        "check_phony": True
    },
    "test_checks": {
        "test_frameworks": ["pytest", "unittest", "nose", "tox"],
        "test_patterns": ["test_*.py", "*_test.py", "tests/*.py"],
        "coverage_tools": ["coverage", "pytest-cov"],
        "min_coverage": 70
    },
    "ci_cd_checks": {
        "github_actions": [".github/workflows/*.yml", ".github/workflows/*.yaml"],
        "jenkins": ["Jenkinsfile", "jenkins/**"],
        "travis": [".travis.yml"],
        "circleci": [".circleci/config.yml"]
    },
    "docker_checks": {
        "dockerfile": ["Dockerfile", "docker/Dockerfile"],
        "compose": ["docker-compose.yml", "docker-compose.yaml"],
        "dockerignore": [".dockerignore"]
    }
}

# Contribution templates configuration
CONTRIBUTION_CONFIG = {
    "readme_improvements": {
        "add_badges": True,
        "add_table_of_contents": True,
        "add_installation_section": True,
        "add_usage_examples": True,
        "add_contributing_guidelines": True,
        "improve_formatting": True
    },
    "makefile_template": {
        "include_help": True,
        "include_testing": True,
        "include_linting": True,
        "include_docker": True,
        "include_ci": True
    },
    "testing_setup": {
        "pytest_config": True,
        "coverage_config": True,
        "github_actions": True,
        "pre_commit_hooks": True
    }
}

# Email templates configuration
EMAIL_CONFIG = {
    "templates": {
        "initial_contact": {
            "subject": "Open Source Contribution - {repo_name}",
            "tone": "professional",
            "max_length": 200
        },
        "follow_up": {
            "subject": "Re: Open Source Contribution - {repo_name}",
            "tone": "friendly",
            "max_length": 150
        },
        "job_inquiry": {
            "subject": "DevOps Engineer Position - Portfolio Review",
            "tone": "professional",
            "max_length": 250
        }
    },
    "personalization": {
        "use_company_name": True,
        "reference_recent_commits": True,
        "mention_specific_repos": True,
        "include_contribution_summary": True
    }
}

# Report generation configuration
REPORT_CONFIG = {
    "formats": ["csv", "html", "json", "pdf"],
    "charts": {
        "company_distribution": True,
        "repo_quality_metrics": True,
        "contribution_opportunities": True,
        "success_timeline": True
    },
    "metrics": {
        "response_rate": True,
        "pr_acceptance_rate": True,
        "interview_conversion": True,
        "time_to_response": True
    }
}