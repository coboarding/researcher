#!/usr/bin/env python3
"""
Company Analysis Script for DevOps Researcher
Focused analysis of specific companies and their repositories.
"""
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel

from config.settings import settings
from src.github_client import GitHubClient
from src.repo_analyzer import RepositoryAnalyzer, AnalysisResult
from src.report_generator import ReportGenerator

console = Console()
logger = logging.getLogger(__name__)


class CompanyAnalyzer:
    """
    Specialized analyzer for individual companies
    """
    
    def __init__(self):
        self.github = GitHubClient()
        self.analyzer = RepositoryAnalyzer(self.github)
        self.report_generator = ReportGenerator()
        settings.create_directories()
    
    def analyze_company_detailed(self, github_org: str, 
                               include_private: bool = False,
                               language_filter: Optional[str] = None,
                               min_stars: int = 0,
                               max_repos: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform detailed analysis of a single company
        """
        console.print(f"[bold cyan]🔍 Detailed Analysis: {github_org}[/bold cyan]")
        
        try:
            # Get organization information
            org_info = self.github.get_organization(github_org)
            if not org_info:
                console.print(f"[red]❌ Organization '{github_org}' not found[/red]")
                return {'success': False, 'error': 'Organization not found'}
            
            # Display organization info
            self._display_org_info(org_info)
            
            # Get repositories with filters
            repos = self._get_filtered_repos(
                github_org, 
                language_filter=language_filter,
                min_stars=min_stars,
                max_repos=max_repos
            )
            
            if not repos:
                console.print("[yellow]⚠️  No repositories found matching criteria[/yellow]")
                return {'success': True, 'repositories': [], 'analyses': []}
            
            console.print(f"[green]✅ Found {len(repos)} repositories to analyze[/green]")
            
            # Analyze repositories
            analyses = []
            
            with Progress() as progress:
                task = progress.add_task(
                    f"[cyan]Analyzing {github_org} repositories...", 
                    total=len(repos)
                )
                
                for repo in repos:
                    try:
                        analysis = self.analyzer.analyze_repository(github_org, repo['name'])
                        analyses.append(analysis)
                        
                        # Show progress for high-value repos
                        if analysis.contribution_potential_score > 60:
                            console.print(f"  🎯 {repo['name']} - High potential ({analysis.contribution_potential_score:.1f})")
                        
                    except Exception as e:
                        logger.error(f"Error analyzing {repo['name']}: {e}")
                    
                    progress.advance(task)
            
            # Generate detailed analysis
            results = self._generate_detailed_analysis(github_org, org_info, repos, analyses)
            
            return {
                'success': True,
                'organization': github_org,
                'org_info': org_info,
                'repositories': repos,
                'analyses': analyses,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in detailed analysis: {e}")
            return {'success': False, 'error': str(e)}
    
    def compare_companies(self, companies: List[str]) -> Dict[str, Any]:
        """
        Compare multiple companies side by side
        """
        console.print(f"[bold cyan]📊 Comparing {len(companies)} companies[/bold cyan]")
        
        company_results = {}
        all_analyses = []
        
        for company in companies:
            console.print(f"\n[bold]Analyzing {company}...[/bold]")
            
            try:
                # Quick analysis of company
                repos = self.github.get_organization_repos(company, per_page=20)
                analyses = []
                
                for repo in repos[:10]:  # Limit for comparison
                    try:
                        analysis = self.analyzer.analyze_repository(company, repo['name'])
                        analyses.append(analysis)
                        all_analyses.append(analysis)
                    except Exception as e:
                        logger.warning(f"Skipping {repo['name']}: {e}")
                
                company_results[company] = {
                    'total_repos': len(repos),
                    'analyzed_repos': len(analyses),
                    'avg_quality': sum(a.overall_quality_score for a in analyses) / len(analyses) if analyses else 0,
                    'avg_potential': sum(a.contribution_potential_score for a in analyses) / len(analyses) if analyses else 0,
                    'high_potential_repos': len([a for a in analyses if a.contribution_potential_score > 70]),
                    'analyses': analyses
                }
                
            except Exception as e:
                logger.error(f"Error analyzing {company}: {e}")
                company_results[company] = {'error': str(e)}
        
        # Display comparison
        self._display_company_comparison(company_results)
        
        # Generate comparison report
        if all_analyses:
            report_files = self.report_generator.generate_analysis_report(all_analyses)
            console.print(f"\n[green]📊 Comparison report generated: {report_files.get('html', 'N/A')}[/green]")
        
        return {
            'success': True,
            'companies': company_results,
            'total_analyses': len(all_analyses)
        }
    
    def find_top_opportunities(self, companies: List[str], 
                              min_potential: float = 60.0,
                              limit: int = 20) -> List[AnalysisResult]:
        """
        Find top contribution opportunities across companies
        """
        console.print(f"[bold cyan]🎯 Finding top opportunities (min score: {min_potential})[/bold cyan]")
        
        all_opportunities = []
        
        with Progress() as progress:
            company_task = progress.add_task("[cyan]Scanning companies...", total=len(companies))
            
            for company in companies:
                try:
                    repos = self.github.get_organization_repos(company, per_page=30)
                    
                    repo_task = progress.add_task(f"[green]Analyzing {company}...", total=len(repos))
                    
                    for repo in repos:
                        try:
                            analysis = self.analyzer.analyze_repository(company, repo['name'])
                            
                            if analysis.contribution_potential_score >= min_potential:
                                all_opportunities.append(analysis)
                            
                        except Exception as e:
                            logger.debug(f"Skipping {company}/{repo['name']}: {e}")
                        
                        progress.advance(repo_task)
                    
                    progress.remove_task(repo_task)
                    
                except Exception as e:
                    logger.error(f"Error scanning {company}: {e}")
                
                progress.advance(company_task)
        
        # Sort by potential score
        top_opportunities = sorted(
            all_opportunities, 
            key=lambda x: x.contribution_potential_score, 
            reverse=True
        )[:limit]
        
        # Display results
        self._display_top_opportunities(top_opportunities)
        
        return top_opportunities
    
    def _get_filtered_repos(self, github_org: str, 
                           language_filter: Optional[str] = None,
                           min_stars: int = 0,
                           max_repos: Optional[int] = None) -> List[Dict]:
        """Get repositories with applied filters"""
        
        # Get all repositories
        repos = self.github.get_organization_repos(github_org, per_page=100)
        
        # Apply filters
        filtered_repos = []
        
        for repo in repos:
            # Star filter
            if repo.get('stargazers_count', 0) < min_stars:
                continue
            
            # Language filter
            if language_filter and repo.get('language', '').lower() != language_filter.lower():
                continue
            
            # Skip forks if not specifically requested
            if repo.get('fork', False):
                continue
            
            filtered_repos.append(repo)
        
        # Apply limit
        if max_repos:
            filtered_repos = filtered_repos[:max_repos]
        
        return filtered_repos
    
    def _display_org_info(self, org_info: Dict) -> None:
        """Display organization information"""
        
        info_text = f"""
[bold]Organization:[/bold] {org_info.get('name', 'N/A')}
[bold]Description:[/bold] {org_info.get('description', 'No description')}
[bold]Location:[/bold] {org_info.get('location', 'Not specified')}
[bold]Website:[/bold] {org_info.get('blog', 'Not specified')}
[bold]Public Repos:[/bold] {org_info.get('public_repos', 0)}
[bold]Followers:[/bold] {org_info.get('followers', 0)}
[bold]Created:[/bold] {org_info.get('created_at', 'Unknown')[:10]}
"""
        
        console.print(Panel(info_text, title=f"🏢 {org_info.get('login', 'Organization')}", border_style="blue"))
    
    def _generate_detailed_analysis(self, github_org: str, org_info: Dict,
                                   repos: List[Dict], analyses: List[AnalysisResult]) -> Dict:
        """Generate detailed analysis results"""
        
        if not analyses:
            return {}
        
        # Calculate metrics
        metrics = {
            'total_repos': len(repos),
            'analyzed_repos': len(analyses),
            'avg_quality_score': sum(a.overall_quality_score for a in analyses) / len(analyses),
            'avg_contribution_potential': sum(a.contribution_potential_score for a in analyses) / len(analyses),
            'total_stars': sum(r.get('stargazers_count', 0) for r in repos),
            'total_forks': sum(r.get('forks_count', 0) for r in repos),
            'languages': {},
            'quality_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'contribution_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'missing_features': {
                'readme': 0, 'makefile': 0, 'tests': 0, 
                'ci_cd': 0, 'docker': 0, 'linting': 0
            }
        }
        
        # Calculate distributions and missing features
        for analysis in analyses:
            # Language distribution
            lang = analysis.language or 'Unknown'
            metrics['languages'][lang] = metrics['languages'].get(lang, 0) + 1
            
            # Quality distribution
            if analysis.overall_quality_score >= 70:
                metrics['quality_distribution']['high'] += 1
            elif analysis.overall_quality_score >= 40:
                metrics['quality_distribution']['medium'] += 1
            else:
                metrics['quality_distribution']['low'] += 1
            
            # Contribution potential distribution
            if analysis.contribution_potential_score >= 70:
                metrics['contribution_distribution']['high'] += 1
            elif analysis.contribution_potential_score >= 40:
                metrics['contribution_distribution']['medium'] += 1
            else:
                metrics['contribution_distribution']['low'] += 1
            
            # Missing features
            if not analysis.has_readme:
                metrics['missing_features']['readme'] += 1
            if not analysis.has_makefile:
                metrics['missing_features']['makefile'] += 1
            if not analysis.has_tests:
                metrics['missing_features']['tests'] += 1
            if not analysis.has_ci_cd:
                metrics['missing_features']['ci_cd'] += 1
            if not analysis.has_docker:
                metrics['missing_features']['docker'] += 1
            if not analysis.has_linting:
                metrics['missing_features']['linting'] += 1
        
        # Display metrics
        self._display_analysis_metrics(github_org, metrics, analyses)
        
        return metrics
    
    def _display_analysis_metrics(self, company: str, metrics: Dict, analyses: List[AnalysisResult]) -> None:
        """Display detailed analysis metrics"""
        
        # Overview table
        table = Table(title=f"📊 {company} Analysis Overview")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Repositories", str(metrics['total_repos']))
        table.add_row("Analyzed Repositories", str(metrics['analyzed_repos']))
        table.add_row("Average Quality Score", f"{metrics['avg_quality_score']:.1f}/100")
        table.add_row("Average Contribution Potential", f"{metrics['avg_contribution_potential']:.1f}/100")
        table.add_row("Total Stars", f"{metrics['total_stars']:,}")
        table.add_row("Total Forks", f"{metrics['total_forks']:,}")
        
        console.print(table)
        
        # Language distribution
        if metrics['languages']:
            console.print("\n[bold]🔤 Language Distribution:[/bold]")
            sorted_langs = sorted(metrics['languages'].items(), key=lambda x: x[1], reverse=True)
            for lang, count in sorted_langs[:10]:
                percentage = (count / metrics['analyzed_repos']) * 100
                console.print(f"  {lang}: {count} repos ({percentage:.1f}%)")
        
        # Missing features analysis
        console.print("\n[bold]⚠️  Missing Features Analysis:[/bold]")
        for feature, count in metrics['missing_features'].items():
            if count > 0:
                percentage = (count / metrics['analyzed_repos']) * 100
                console.print(f"  {feature.replace('_', ' ').title()}: {count} repos ({percentage:.1f}%)")
        
        # Top opportunities
        top_opportunities = sorted(analyses, key=lambda x: x.contribution_potential_score, reverse=True)[:10]
        
        if top_opportunities:
            console.print("\n[bold]🎯 Top Contribution Opportunities:[/bold]")
            
            opp_table = Table()
            opp_table.add_column("Rank", width=4)
            opp_table.add_column("Repository", style="green")
            opp_table.add_column("Score", style="yellow", justify="right")
            opp_table.add_column("Language", style="blue")
            opp_table.add_column("Stars", style="cyan", justify="right")
            
            for i, analysis in enumerate(top_opportunities, 1):
                score = analysis.contribution_potential_score
                emoji = "🔥" if score > 80 else "⭐" if score > 60 else "💡"
                
                opp_table.add_row(
                    f"{emoji} {i}",
                    analysis.repo_name,
                    f"{score:.1f}",
                    analysis.language or "Unknown",
                    str(analysis.stars)
                )
            
            console.print(opp_table)
    
    def _display_company_comparison(self, company_results: Dict) -> None:
        """Display comparison between companies"""
        
        # Create comparison table
        table = Table(title="🏆 Company Comparison")
        table.add_column("Company", style="magenta")
        table.add_column("Repos", style="cyan", justify="right")
        table.add_column("Avg Quality", style="green", justify="right")
        table.add_column("Avg Potential", style="yellow", justify="right")
        table.add_column("High Potential", style="red", justify="right")
        table.add_column("Status", style="blue")
        
        # Sort companies by average quality
        sorted_companies = sorted(
            company_results.items(),
            key=lambda x: x[1].get('avg_quality', 0) if 'error' not in x[1] else 0,
            reverse=True
        )
        
        for company, results in sorted_companies:
            if 'error' in results:
                table.add_row(company, "N/A", "N/A", "N/A", "N/A", "❌ Error")
            else:
                table.add_row(
                    company,
                    str(results['analyzed_repos']),
                    f"{results['avg_quality']:.1f}",
                    f"{results['avg_potential']:.1f}",
                    str(results['high_potential_repos']),
                    "✅ Success"
                )
        
        console.print(table)
        
        # Recommendations
        console.print("\n[bold cyan]💡 Recommendations:[/bold cyan]")
        
        # Find best company for contributions
        best_company = max(
            [(k, v) for k, v in company_results.items() if 'error' not in v],
            key=lambda x: x[1].get('avg_potential', 0),
            default=None
        )
        
        if best_company:
            console.print(f"🎯 Best for contributions: [bold]{best_company[0]}[/bold] (avg potential: {best_company[1]['avg_potential']:.1f})")
        
        # Find highest quality
        highest_quality = max(
            [(k, v) for k, v in company_results.items() if 'error' not in v],
            key=lambda x: x[1].get('avg_quality', 0),
            default=None
        )
        
        if highest_quality:
            console.print(f"🏆 Highest quality: [bold]{highest_quality[0]}[/bold] (avg quality: {highest_quality[1]['avg_quality']:.1f})")
    
    def _display_top_opportunities(self, opportunities: List[AnalysisResult]) -> None:
        """Display top contribution opportunities"""
        
        if not opportunities:
            console.print("[yellow]⚠️  No opportunities found matching criteria[/yellow]")
            return
        
        console.print(f"\n[bold green]🎯 Found {len(opportunities)} Top Opportunities[/bold green]")
        
        # Create opportunities table
        table = Table(title="🔥 Best Contribution Opportunities")
        table.add_column("Rank", width=6)
        table.add_column("Company", style="magenta")
        table.add_column("Repository", style="green")
        table.add_column("Score", style="yellow", justify="right")
        table.add_column("Language", style="blue")
        table.add_column("Stars", style="cyan", justify="right")
        table.add_column("Issues", style="red", justify="right")
        
        for i, opp in enumerate(opportunities, 1):
            score = opp.contribution_potential_score
            emoji = "🔥" if score > 80 else "⭐" if score > 70 else "💡"
            
            table.add_row(
                f"{emoji} {i}",
                opp.owner,
                opp.repo_name,
                f"{score:.1f}",
                opp.language or "Unknown",
                str(opp.stars),
                str(len(opp.help_wanted_issues))
            )
        
        console.print(table)
        
        # Show opportunity breakdown
        console.print("\n[bold]📋 Opportunity Breakdown:[/bold]")
        
        missing_counts = {}
        for opp in opportunities:
            for opportunity in opp.contribution_opportunities:
                missing_counts[opportunity] = missing_counts.get(opportunity, 0) + 1
        
        sorted_missing = sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)
        for opportunity, count in sorted_missing:
            console.print(f"  • {opportunity}: {count} repositories")


def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command line arguments"""
    parser = argparse.ArgumentParser(
        description="Analyze specific companies in detail",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Main commands
    subparsers = parser.add_subparsers(dest='command', help='Analysis commands')
    
    # Single company analysis
    single_parser = subparsers.add_parser('single', help='Analyze single company in detail')
    single_parser.add_argument('company', help='GitHub organization name')
    single_parser.add_argument('--language', help='Filter by programming language')
    single_parser.add_argument('--min-stars', type=int, default=0, help='Minimum stars')
    single_parser.add_argument('--max-repos', type=int, help='Maximum repositories to analyze')
    
    # Company comparison
    compare_parser = subparsers.add_parser('compare', help='Compare multiple companies')
    compare_parser.add_argument('companies', nargs='+', help='Companies to compare')
    
    # Find opportunities
    opportunities_parser = subparsers.add_parser('opportunities', help='Find top opportunities')
    opportunities_parser.add_argument('companies', nargs='+', help='Companies to scan')
    opportunities_parser.add_argument('--min-score', type=float, default=60.0, help='Minimum potential score')
    opportunities_parser.add_argument('--limit', type=int, default=20, help='Maximum results')
    
    # Report generation
    report_parser = subparsers.add_parser('report', help='Generate detailed reports')
    report_parser.add_argument('companies', nargs='+', help='Companies to include')
    report_parser.add_argument('--format', choices=['csv', 'html', 'json'], default='html')
    
    return parser


def main():
    """Main entry point"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
    
    analyzer = CompanyAnalyzer()
    
    try:
        if args.command == 'single':
            result = analyzer.analyze_company_detailed(
                args.company,
                language_filter=getattr(args, 'language', None),
                min_stars=getattr(args, 'min_stars', 0),
                max_repos=getattr(args, 'max_repos', None)
            )
            
        elif args.command == 'compare':
            result = analyzer.compare_companies(args.companies)
            
        elif args.command == 'opportunities':
            opportunities = analyzer.find_top_opportunities(
                args.companies,
                min_potential=args.min_score,
                limit=args.limit
            )
            result = {'success': True, 'opportunities': opportunities}
            
        elif args.command == 'report':
            # Generate comprehensive report
            console.print("[yellow]Report generation not implemented in this script[/yellow]")
            console.print("Use main.py --companies for full report generation")
            return 1
        
        if result.get('success'):
            console.print("\n[bold green]✅ Analysis completed successfully![/bold green]")
        else:
            console.print(f"\n[bold red]❌ Analysis failed: {result.get('error')}[/bold red]")
            return 1
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Analysis interrupted[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]💥 Error: {e}[/bold red]")
        logger.error(f"Unexpected error: {e}")
        return 1