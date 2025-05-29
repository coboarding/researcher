"""
Basic tests for DevOps Researcher
"""
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.github_client import GitHubClient
from src.repo_analyzer import RepositoryAnalyzer, AnalysisResult
from src.contribution_generator import ContributionGenerator
from src.report_generator import ReportGenerator
from src.email_templates import EmailTemplateManager
from config.settings import settings


class TestBasicImports:
    """Test that all modules can be imported"""

    def test_import_github_client(self):
        """Test that GitHubClient can be imported and instantiated"""
        client = GitHubClient()
        assert client is not None
        assert hasattr(client, 'api_url')

    def test_import_repo_analyzer(self):
        """Test that RepositoryAnalyzer can be imported"""
        github_client = GitHubClient()
        analyzer = RepositoryAnalyzer(github_client)
        assert analyzer is not None
        assert analyzer.github is not None

    def test_import_contribution_generator(self):
        """Test that ContributionGenerator can be imported"""
        generator = ContributionGenerator()
        assert generator is not None

    def test_import_report_generator(self):
        """Test that ReportGenerator can be imported"""
        generator = ReportGenerator()
        assert generator is not None

    def test_import_email_templates(self):
        """Test that EmailTemplateManager can be imported"""
        manager = EmailTemplateManager()
        assert manager is not None
        assert len(manager.templates) > 0


class TestAnalysisResult:
    """Test AnalysisResult data structure"""

    def test_analysis_result_creation(self):
        """Test creating an AnalysisResult"""
        result = AnalysisResult(
            repo_name="test-repo",
            owner="test-owner"
        )

        assert result.repo_name == "test-repo"
        assert result.owner == "test-owner"
        assert result.overall_quality_score == 0.0
        assert result.contribution_potential_score == 0.0
        assert isinstance(result.readme_issues, list)
        assert isinstance(result.contribution_opportunities, list)

    def test_analysis_result_to_dict(self):
        """Test converting AnalysisResult to dictionary"""
        result = AnalysisResult(
            repo_name="test-repo",
            owner="test-owner"
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict['repo_name'] == "test-repo"
        assert result_dict['owner'] == "test-owner"


class TestSettings:
    """Test configuration settings"""

    def test_settings_loaded(self):
        """Test that settings are loaded correctly"""
        assert settings.app_name == "DevOps Researcher"
        assert settings.app_version == "1.0.0"
        assert settings.github_api_url == "https://api.github.com"

    def test_settings_directories(self):
        """Test directory creation"""
        # This should not raise an exception
        settings.create_directories()

        # Check that directories exist or can be created
        assert settings.output_dir
        assert settings.reports_dir
        assert settings.contributions_dir


class TestEmailTemplates:
    """Test email template functionality"""

    def test_template_loading(self):
        """Test that email templates are loaded"""
        manager = EmailTemplateManager()
        template_names = manager.get_template_names()

        assert 'initial_contact' in template_names
        assert 'follow_up' in template_names
        assert 'job_inquiry' in template_names

    def test_template_info(self):
        """Test getting template information"""
        manager = EmailTemplateManager()
        info = manager.get_template_info('initial_contact')

        assert 'name' in info
        assert 'tone' in info
        assert 'max_length' in info

    def test_context_validation(self):
        """Test context validation for templates"""
        manager = EmailTemplateManager()

        # Test with missing required variables
        missing = manager.validate_context('initial_contact', {})
        assert len(missing) > 0

        # Test with complete context
        complete_context = {
            'company': 'TestCompany',
            'repo_name': 'test-repo',
            'contribution_summary': 'test improvements',
            'your_name': 'Test User'
        }
        missing = manager.validate_context('initial_contact', complete_context)
        assert len(missing) == 0


class TestIntegration:
    """Integration tests (require network access)"""

    @pytest.mark.skip(reason="Requires GitHub API access")
    def test_github_connection(self):
        """Test GitHub API connection"""
        client = GitHubClient()
        success = client.test_connection()
        assert success is True or success is False  # Should not raise exception

    @pytest.mark.skip(reason="Requires GitHub API access")
    def test_repository_analysis(self):
        """Test analyzing a real repository"""
        client = GitHubClient()
        analyzer = RepositoryAnalyzer(client)

        # Test with a small, known repository
        result = analyzer.analyze_repository('octocat', 'Hello-World')

        assert result.repo_name == 'Hello-World'
        assert result.owner == 'octocat'
        assert result.overall_quality_score >= 0
        assert result.contribution_potential_score >= 0


if __name__ == "__main__":
    pytest.main([__file__])