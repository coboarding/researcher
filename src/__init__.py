"""
DevOps Researcher - Source Package
Automated analysis and contribution generation for German DevOps companies.
"""

__version__ = "1.0.0"
__author__ = "DevOps Researcher"
__description__ = "Automated GitHub repository analysis and contribution generation"

from .github_client import GitHubClient
from .repo_analyzer import RepositoryAnalyzer, AnalysisResult
from .contribution_generator import ContributionGenerator, ContributionPlan
from .report_generator import ReportGenerator
from .email_templates import EmailTemplateManager

__all__ = [
    'GitHubClient',
    'RepositoryAnalyzer',
    'AnalysisResult',
    'ContributionGenerator',
    'ContributionPlan',
    'ReportGenerator',
    'EmailTemplateManager'
]