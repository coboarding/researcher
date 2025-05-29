"""
GitHub API Client for DevOps Researcher
Handles all interactions with GitHub API including rate limiting, caching, and retries.
"""
import time
import json
import base64
import logging
from typing import Optional, Dict, List, Any, Union
from pathlib import Path
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when GitHub API rate limit is exceeded"""
    pass


class GitHubAPIError(Exception):
    """Raised when GitHub API returns an error"""
    pass


class GitHubClient:
    """
    GitHub API client with rate limiting, caching, and retry logic
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.github_token
        self.api_url = settings.github_api_url
        self.session = self._create_session()
        self.cache_dir = Path(settings.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Rate limiting
        self.requests_made = 0
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = datetime.now()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()

        # Headers
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': f'{settings.app_name}/{settings.app_version}'
        }
        if self.token:
            headers['Authorization'] = f'token {self.token}'

        session.headers.update(headers)

        # Retry strategy
        retry_strategy = Retry(
            total=settings.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for given key"""
        return self.cache_dir / f"{cache_key.replace('/', '_')}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False

        if not settings.cache_enabled:
            return False

        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        max_age = timedelta(hours=settings.cache_duration_hours)

        return cache_age < max_age

    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load data from cache if valid"""
        cache_path = self._get_cache_path(cache_key)

        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                logger.debug(f"Cache hit for {cache_key}")
                return data
            except (json.JSONDecodeError, FileNotFoundError):
                logger.warning(f"Invalid cache file: {cache_path}")
                cache_path.unlink(missing_ok=True)

        return None

    def _save_to_cache(self, cache_key: str, data: Dict) -> None:
        """Save data to cache"""
        if not settings.cache_enabled:
            return

        cache_path = self._get_cache_path(cache_key)

        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Cached data for {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")

    def _check_rate_limit(self) -> None:
        """Check and handle rate limiting"""
        if datetime.now() < self.rate_limit_reset and self.rate_limit_remaining <= 1:
            sleep_time = (self.rate_limit_reset - datetime.now()).total_seconds()
            logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time + 1)

    def _update_rate_limit_info(self, response: requests.Response) -> None:
        """Update rate limit information from response headers"""
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])

        if 'X-RateLimit-Reset' in response.headers:
            reset_timestamp = int(response.headers['X-RateLimit-Reset'])
            self.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)

    def _make_request(self, endpoint: str, params: Optional[Dict] = None,
                     use_cache: bool = True) -> Dict:
        """Make API request with caching and rate limiting"""

        # Create cache key
        cache_key = f"{endpoint}_{hash(str(params or {}))}"

        # Try cache first
        if use_cache:
            cached_data = self._load_from_cache(cache_key)
            if cached_data is not None:
                return cached_data

        # Check rate limit
        self._check_rate_limit()

        # Make request
        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.get(url, params=params)
            self._update_rate_limit_info(response)

            if response.status_code == 429:
                raise RateLimitExceeded("GitHub API rate limit exceeded")
            elif response.status_code == 404:
                return {}
            elif not response.ok:
                raise GitHubAPIError(f"API error {response.status_code}: {response.text}")

            data = response.json()

            # Cache successful response
            if use_cache:
                self._save_to_cache(cache_key, data)

            # Add delay to respect rate limits
            time.sleep(settings.analysis_delay_seconds)

            return data

        except requests.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            raise GitHubAPIError(f"Request failed: {e}")

    def test_connection(self) -> bool:
        """Test GitHub API connection and token validity"""
        try:
            data = self._make_request('/user', use_cache=False)
            if 'login' in data:
                logger.info(f"Connected to GitHub as: {data['login']}")
                return True
            else:
                logger.info("Connected to GitHub (unauthenticated)")
                return True
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False

    def get_organization(self, org_name: str) -> Dict:
        """Get organization information"""
        return self._make_request(f'/orgs/{org_name}')

    def get_organization_repos(self, org_name: str, per_page: int = 100) -> List[Dict]:
        """Get all repositories for an organization"""
        repos = []
        page = 1

        while len(repos) < settings.max_repos_per_org:
            params = {'per_page': per_page, 'page': page, 'sort': 'updated'}
            data = self._make_request(f'/orgs/{org_name}/repos', params)

            if not data or not isinstance(data, list):
                break

            repos.extend(data)

            if len(data) < per_page:
                break

            page += 1

        return repos[:settings.max_repos_per_org]

    def get_repository(self, owner: str, repo: str) -> Dict:
        """Get repository information"""
        return self._make_request(f'/repos/{owner}/{repo}')

    def get_file_content(self, owner: str, repo: str, path: str,
                        ref: str = 'main') -> Optional[str]:
        """Get file content from repository"""
        try:
            data = self._make_request(f'/repos/{owner}/{repo}/contents/{path}')

            if 'content' in data and data['encoding'] == 'base64':
                content = base64.b64decode(data['content']).decode('utf-8')
                return content
        except GitHubAPIError:
            # Try with master branch if main doesn't exist
            if ref == 'main':
                return self.get_file_content(owner, repo, path, 'master')

        return None

    def get_repository_tree(self, owner: str, repo: str,
                           ref: str = 'main', recursive: bool = True) -> List[Dict]:
        """Get repository file tree"""
        params = {'recursive': '1' if recursive else '0'}
        try:
            data = self._make_request(f'/repos/{owner}/{repo}/git/trees/{ref}', params)
            return data.get('tree', [])
        except GitHubAPIError:
            # Try with master branch
            if ref == 'main':
                return self.get_repository_tree(owner, repo, 'master', recursive)
            return []

    def get_issues(self, owner: str, repo: str, labels: Optional[List[str]] = None,
                  state: str = 'open') -> List[Dict]:
        """Get repository issues"""
        params = {'state': state, 'per_page': 100}
        if labels:
            params['labels'] = ','.join(labels)

        data = self._make_request(f'/repos/{owner}/{repo}/issues', params)
        return data if isinstance(data, list) else []

    def get_pull_requests(self, owner: str, repo: str, state: str = 'open') -> List[Dict]:
        """Get repository pull requests"""
        params = {'state': state, 'per_page': 100}
        data = self._make_request(f'/repos/{owner}/{repo}/pulls', params)
        return data if isinstance(data, list) else []

    def get_commits(self, owner: str, repo: str, since: Optional[str] = None,
                   per_page: int = 100) -> List[Dict]:
        """Get repository commits"""
        params = {'per_page': per_page}
        if since:
            params['since'] = since

        data = self._make_request(f'/repos/{owner}/{repo}/commits', params)
        return data if isinstance(data, list) else []

    def get_contributors(self, owner: str, repo: str) -> List[Dict]:
        """Get repository contributors"""
        data = self._make_request(f'/repos/{owner}/{repo}/contributors')
        return data if isinstance(data, list) else []

    def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get repository programming languages"""
        data = self._make_request(f'/repos/{owner}/{repo}/languages')
        return data if isinstance(data, dict) else {}

    def search_repositories(self, query: str, sort: str = 'updated',
                           per_page: int = 100) -> List[Dict]:
        """Search repositories"""
        params = {
            'q': query,
            'sort': sort,
            'per_page': per_page
        }

        data = self._make_request('/search/repositories', params)
        return data.get('items', []) if isinstance(data, dict) else []

    def search_organizations(self, query: str, per_page: int = 100) -> List[Dict]:
        """Search organizations"""
        params = {
            'q': query + ' type:org',
            'per_page': per_page
        }

        data = self._make_request('/search/users', params)
        return data.get('items', []) if isinstance(data, dict) else []

    def fork_repository(self, owner: str, repo: str, organization: Optional[str] = None) -> Dict:
        """Fork a repository"""
        endpoint = f'/repos/{owner}/{repo}/forks'
        data = {}
        if organization:
            data['organization'] = organization

        response = self.session.post(f"{self.api_url}/{endpoint.lstrip('/')}", json=data)

        if not response.ok:
            raise GitHubAPIError(f"Failed to fork repository: {response.text}")

        return response.json()

    def create_pull_request(self, owner: str, repo: str, title: str, body: str,
                           head: str, base: str = 'main') -> Dict:
        """Create a pull request"""
        endpoint = f'/repos/{owner}/{repo}/pulls'
        data = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }

        response = self.session.post(f"{self.api_url}/{endpoint.lstrip('/')}", json=data)

        if not response.ok:
            raise GitHubAPIError(f"Failed to create pull request: {response.text}")

        return response.json()

    def create_issue(self, owner: str, repo: str, title: str, body: str,
                    labels: Optional[List[str]] = None) -> Dict:
        """Create an issue"""
        endpoint = f'/repos/{owner}/{repo}/issues'
        data = {
            'title': title,
            'body': body
        }
        if labels:
            data['labels'] = labels

        response = self.session.post(f"{self.api_url}/{endpoint.lstrip('/')}", json=data)

        if not response.ok:
            raise GitHubAPIError(f"Failed to create issue: {response.text}")

        return response.json()

    def get_workflow_runs(self, owner: str, repo: str) -> List[Dict]:
        """Get GitHub Actions workflow runs"""
        data = self._make_request(f'/repos/{owner}/{repo}/actions/runs')
        return data.get('workflow_runs', []) if isinstance(data, dict) else []

    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status"""
        return {
            'remaining': self.rate_limit_remaining,
            'reset_time': self.rate_limit_reset.isoformat(),
            'requests_made': self.requests_made
        }

    def clear_cache(self) -> None:
        """Clear all cached data"""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
            logger.info("Cache cleared")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.cache_dir.exists():
            return {'files': 0, 'total_size': 0}

        cache_files = list(self.cache_dir.glob('*.json'))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            'files': len(cache_files),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }