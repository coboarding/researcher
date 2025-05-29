"""
Repository Analyzer for DevOps Researcher
Analyzes repositories for potential improvements and contribution opportunities.
"""
import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from src.github_client import GitHubClient
from config.settings import ANALYSIS_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Container for repository analysis results"""
    repo_name: str
    owner: str
    analysis_date: datetime = field(default_factory=datetime.now)

    # Basic repository info
    description: str = ""
    language: str = ""
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    last_updated: Optional[datetime] = None

    # Documentation analysis
    has_readme: bool = False
    readme_quality_score: float = 0.0
    readme_issues: List[str] = field(default_factory=list)

    # Build system analysis
    has_makefile: bool = False
    makefile_quality_score: float = 0.0
    makefile_issues: List[str] = field(default_factory=list)

    # Testing analysis
    has_tests: bool = False
    test_framework: Optional[str] = None
    test_coverage_info: bool = False
    testing_issues: List[str] = field(default_factory=list)

    # CI/CD analysis
    has_ci_cd: bool = False
    ci_cd_platform: Optional[str] = None
    ci_cd_issues: List[str] = field(default_factory=list)

    # Docker analysis
    has_docker: bool = False
    docker_issues: List[str] = field(default_factory=list)

    # Code quality analysis
    has_linting: bool = False
    has_formatting: bool = False
    code_quality_issues: List[str] = field(default_factory=list)

    # Contribution opportunities
    help_wanted_issues: List[Dict] = field(default_factory=list)
    good_first_issues: List[Dict] = field(default_factory=list)
    contribution_opportunities: List[str] = field(default_factory=list)

    # Overall scores
    overall_quality_score: float = 0.0
    contribution_potential_score: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


class RepositoryAnalyzer:
    """
    Analyzes GitHub repositories for quality and contribution opportunities
    """

    def __init__(self, github_client: GitHubClient):
        self.github = github_client
        self.analysis_config = ANALYSIS_CONFIG

    def analyze_repository(self, owner: str, repo_name: str) -> AnalysisResult:
        """
        Perform comprehensive analysis of a repository
        """
        logger.info(f"Analyzing repository: {owner}/{repo_name}")

        result = AnalysisResult(repo_name=repo_name, owner=owner)

        try:
            # Get basic repository information
            repo_info = self.github.get_repository(owner, repo_name)
            if not repo_info:
                logger.warning(f"Repository {owner}/{repo_name} not found")
                return result

            self._extract_basic_info(repo_info, result)

            # Get repository file tree
            file_tree = self.github.get_repository_tree(owner, repo_name)

            # Analyze different aspects
            self._analyze_documentation(owner, repo_name, file_tree, result)
            self._analyze_build_system(owner, repo_name, file_tree, result)
            self._analyze_testing(owner, repo_name, file_tree, result)
            self._analyze_ci_cd(owner, repo_name, file_tree, result)
            self._analyze_docker(owner, repo_name, file_tree, result)
            self._analyze_code_quality(owner, repo_name, file_tree, result)
            self._analyze_issues(owner, repo_name, result)

            # Calculate overall scores
            self._calculate_scores(result)

            # Identify contribution opportunities
            self._identify_contribution_opportunities(result)

            logger.info(f"Analysis completed for {owner}/{repo_name}. "
                       f"Quality score: {result.overall_quality_score:.2f}")

        except Exception as e:
            logger.error(f"Error analyzing {owner}/{repo_name}: {e}")

        return result

    def _extract_basic_info(self, repo_info: Dict, result: AnalysisResult) -> None:
        """Extract basic repository information"""
        result.description = repo_info.get('description', '') or ''
        result.language = repo_info.get('language', '') or ''
        result.stars = repo_info.get('stargazers_count', 0)
        result.forks = repo_info.get('forks_count', 0)
        result.open_issues = repo_info.get('open_issues_count', 0)

        if repo_info.get('updated_at'):
            result.last_updated = datetime.fromisoformat(
                repo_info['updated_at'].replace('Z', '+00:00')
            )

    def _analyze_documentation(self, owner: str, repo_name: str,
                              file_tree: List[Dict], result: AnalysisResult) -> None:
        """Analyze repository documentation"""
        # Check for README file
        readme_files = [f for f in file_tree
                       if f['path'].lower() in ['readme.md', 'readme.rst', 'readme.txt', 'readme']]

        if readme_files:
            result.has_readme = True
            readme_content = self.github.get_file_content(owner, repo_name, readme_files[0]['path'])

            if readme_content:
                result.readme_quality_score, result.readme_issues = self._analyze_readme_content(readme_content)
        else:
            result.readme_issues.append("No README file found")

    def _analyze_readme_content(self, content: str) -> Tuple[float, List[str]]:
        """Analyze README content quality"""
        issues = []
        score = 0.0
        max_score = 100.0

        # Check length
        if len(content) < self.analysis_config['readme_quality_checks']['min_length']:
            issues.append(f"README too short (< {self.analysis_config['readme_quality_checks']['min_length']} chars)")
        else:
            score += 20

        # Check for required sections
        content_lower = content.lower()
        required_sections = self.analysis_config['readme_quality_checks']['required_sections']

        for section in required_sections:
            if section in content_lower:
                score += 15
            else:
                issues.append(f"Missing '{section}' section")

        # Check for badges
        if self.analysis_config['readme_quality_checks']['check_badges']:
            if re.search(r'!\[.*?\]\(.*?\.svg\)', content):
                score += 10
            else:
                issues.append("No badges found (build status, coverage, etc.)")

        # Check for code examples
        if self.analysis_config['readme_quality_checks']['check_examples']:
            if '```' in content or '    ' in content:
                score += 10
            else:
                issues.append("No code examples found")

        # Check for license mention
        if self.analysis_config['readme_quality_checks']['check_license']:
            if 'license' in content_lower:
                score += 10
            else:
                issues.append("No license information found")

        return min(score, max_score), issues

    def _analyze_build_system(self, owner: str, repo_name: str,
                             file_tree: List[Dict], result: AnalysisResult) -> None:
        """Analyze build system (Makefile, etc.)"""
        # Check for Makefile
        makefile_files = [f for f in file_tree
                         if f['path'].lower() in ['makefile', 'makefile.am', 'gnumakefile']]

        if makefile_files:
            result.has_makefile = True
            makefile_content = self.github.get_file_content(owner, repo_name, makefile_files[0]['path'])

            if makefile_content:
                result.makefile_quality_score, result.makefile_issues = self._analyze_makefile_content(makefile_content)
        else:
            result.makefile_issues.append("No Makefile found")

    def _analyze_makefile_content(self, content: str) -> Tuple[float, List[str]]:
        """Analyze Makefile content quality"""
        issues = []
        score = 0.0
        max_score = 100.0

        # Check for required targets
        required_targets = self.analysis_config['makefile_checks']['required_targets']
        for target in required_targets:
            if f"{target}:" in content:
                score += 20
            else:
                issues.append(f"Missing required target: {target}")

        # Check for recommended targets
        recommended_targets = self.analysis_config['makefile_checks']['recommended_targets']
        found_recommended = 0
        for target in recommended_targets:
            if f"{target}:" in content:
                found_recommended += 1

        score += (found_recommended / len(recommended_targets)) * 30

        if found_recommended < len(recommended_targets):
            missing = [t for t in recommended_targets if f"{t}:" not in content]
            issues.append(f"Missing recommended targets: {', '.join(missing)}")

        # Check for .PHONY declarations
        if self.analysis_config['makefile_checks']['check_phony']:
            if '.PHONY:' in content:
                score += 10
            else:
                issues.append("No .PHONY declarations found")

        return min(score, max_score), issues

    def _analyze_testing(self, owner: str, repo_name: str,
                        file_tree: List[Dict], result: AnalysisResult) -> None:
        """Analyze testing setup"""
        # Check for test files
        test_files = []
        test_patterns = self.analysis_config['test_checks']['test_patterns']

        for file_info in file_tree:
            path = file_info['path']
            for pattern in test_patterns:
                if self._matches_pattern(path, pattern):
                    test_files.append(path)
                    break

        if test_files:
            result.has_tests = True
            result.test_framework = self._detect_test_framework(file_tree)
        else:
            result.testing_issues.append("No test files found")

        # Check for test configuration files
        test_config_files = ['pytest.ini', 'tox.ini', 'setup.cfg', '.coveragerc']
        found_configs = [f for f in file_tree
                        if f['path'] in test_config_files]

        if found_configs:
            result.test_coverage_info = True
        else:
            result.testing_issues.append("No test configuration files found")

    def _detect_test_framework(self, file_tree: List[Dict]) -> Optional[str]:
        """Detect which testing framework is used"""
        frameworks = self.analysis_config['test_checks']['test_frameworks']

        for file_info in file_tree:
            path = file_info['path'].lower()

            if 'pytest' in path or 'pytest.ini' in path:
                return 'pytest'
            elif 'unittest' in path:
                return 'unittest'
            elif 'nose' in path:
                return 'nose'
            elif 'tox.ini' in path:
                return 'tox'

        return None

    def _analyze_ci_cd(self, owner: str, repo_name: str,
                      file_tree: List[Dict], result: AnalysisResult) -> None:
        """Analyze CI/CD setup"""
        ci_cd_configs = self.analysis_config['ci_cd_checks']

        for platform, patterns in ci_cd_configs.items():
            for pattern in patterns:
                matching_files = [f for f in file_tree
                                if self._matches_pattern(f['path'], pattern)]
                if matching_files:
                    result.has_ci_cd = True
                    result.ci_cd_platform = platform
                    return

        if not result.has_ci_cd:
            result.ci_cd_issues.append("No CI/CD configuration found")

    def _analyze_docker(self, owner: str, repo_name: str,
                       file_tree: List[Dict], result: AnalysisResult) -> None:
        """Analyze Docker setup"""
        docker_configs = self.analysis_config['docker_checks']

        docker_files_found = []
        for file_type, patterns in docker_configs.items():
            for pattern in patterns:
                matching_files = [f for f in file_tree
                                if self._matches_pattern(f['path'], pattern)]
                if matching_files:
                    docker_files_found.append(file_type)

        if docker_files_found:
            result.has_docker = True

            # Check for complete Docker setup
            if 'dockerfile' not in docker_files_found:
                result.docker_issues.append("Missing Dockerfile")
            if 'dockerignore' not in docker_files_found:
                result.docker_issues.append("Missing .dockerignore")
        else:
            result.docker_issues.append("No Docker configuration found")

    def _analyze_code_quality(self, owner: str, repo_name: str,
                             file_tree: List[Dict], result: AnalysisResult) -> None:
        """Analyze code quality tools setup"""
        # Check for linting configuration
        linting_files = ['.flake8', '.pylintrc', 'pyproject.toml', 'setup.cfg', '.eslintrc']
        found_linting = [f for f in file_tree
                        if f['path'] in linting_files]

        if found_linting:
            result.has_linting = True
        else:
            result.code_quality_issues.append("No linting configuration found")

        # Check for formatting configuration
        formatting_files = ['.black', '.prettierrc', '.editorconfig', 'pyproject.toml']
        found_formatting = [f for f in file_tree
                           if f['path'] in formatting_files]

        if found_formatting:
            result.has_formatting = True
        else:
            result.code_quality_issues.append("No code formatting configuration found")

    def _analyze_issues(self, owner: str, repo_name: str, result: AnalysisResult) -> None:
        """Analyze repository issues for contribution opportunities"""
        # Get help wanted issues
        help_wanted = self.github.get_issues(owner, repo_name, ['help wanted'])
        result.help_wanted_issues = help_wanted

        # Get good first issues
        good_first = self.github.get_issues(owner, repo_name, ['good first issue'])
        result.good_first_issues = good_first

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches a glob-like pattern"""
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.match(regex_pattern, path))
        else:
            return path == pattern

    def _calculate_scores(self, result: AnalysisResult) -> None:
        """Calculate overall quality and contribution potential scores"""
        # Quality score (0-100)
        quality_components = {
            'readme': result.readme_quality_score * 0.25,
            'makefile': result.makefile_quality_score * 0.15 if result.has_makefile else 0,
            'tests': 20 if result.has_tests else 0,
            'ci_cd': 15 if result.has_ci_cd else 0,
            'docker': 10 if result.has_docker else 0,
            'code_quality': 15 if (result.has_linting and result.has_formatting) else 0
        }

        result.overall_quality_score = sum(quality_components.values())

        # Contribution potential score (0-100)
        contribution_components = {
            'missing_readme': 20 if not result.has_readme else 0,
            'readme_issues': len(result.readme_issues) * 5,
            'missing_makefile': 15 if not result.has_makefile else 0,
            'makefile_issues': len(result.makefile_issues) * 3,
            'missing_tests': 20 if not result.has_tests else 0,
            'missing_ci_cd': 15 if not result.has_ci_cd else 0,
            'missing_docker': 10 if not result.has_docker else 0,
            'help_wanted_issues': len(result.help_wanted_issues) * 5,
            'good_first_issues': len(result.good_first_issues) * 3
        }

        result.contribution_potential_score = min(sum(contribution_components.values()), 100)

    def _identify_contribution_opportunities(self, result: AnalysisResult) -> None:
        """Identify specific contribution opportunities"""
        opportunities = []

        if not result.has_readme:
            opportunities.append("Create comprehensive README.md")
        elif result.readme_issues:
            opportunities.append("Improve README.md documentation")

        if not result.has_makefile:
            opportunities.append("Add Makefile with common targets")
        elif result.makefile_issues:
            opportunities.append("Enhance Makefile with missing targets")

        if not result.has_tests:
            opportunities.append("Add test suite")
        elif result.testing_issues:
            opportunities.append("Improve testing configuration")

        if not result.has_ci_cd:
            opportunities.append("Set up CI/CD pipeline")

        if not result.has_docker:
            opportunities.append("Add Docker configuration")

        if result.code_quality_issues:
            opportunities.append("Add code quality tools (linting, formatting)")

        if result.help_wanted_issues:
            opportunities.append(f"Contribute to {len(result.help_wanted_issues)} 'help wanted' issues")

        if result.good_first_issues:
            opportunities.append(f"Work on {len(result.good_first_issues)} 'good first issue' items")

        result.contribution_opportunities = opportunities