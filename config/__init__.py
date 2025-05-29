"""
Configuration package for DevOps Researcher
"""

from .settings import settings, ANALYSIS_CONFIG, CONTRIBUTION_CONFIG, EMAIL_CONFIG, REPORT_CONFIG

__all__ = [
    'settings',
    'ANALYSIS_CONFIG',
    'CONTRIBUTION_CONFIG',
    'EMAIL_CONFIG',
    'REPORT_CONFIG'
]