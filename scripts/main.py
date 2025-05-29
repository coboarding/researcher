#!/usr/bin/env python3
"""
DevOps Researcher - Main Script
Orchestrates the complete analysis and contribution process for German DevOps companies.
"""
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel

from config.settings import settings
from src.github_client import GitHubClient
from src.repo_analyzer import RepositoryAnalyzer, AnalysisResult
from src.contribution_generator import ContributionGenerator, ContributionPlan
from src.report_generator import ReportGenerator
from src.email_templates import EmailTemplateManager

# Setup rich console
console = Console()

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(Path(settings.logs_dir) / "main.log")
    ]
)
logger = logging.getLogger(__name__)


class DevOpsResearcher:
    """
    Main orchestrator for the DevOps research and contribution process
    """
    
    def __init__(self):
        self.console = console
        self.github = GitHubClient()
        self.analyzer = RepositoryAnalyzer(self.github)
        self.contribution_generator = ContributionGenerator()
        self.report_generator = ReportGenerator()
        self.email_manager = EmailTemplateManager()
        
        # Create output directories
        settings.create_directories()
        
        # Statistics
        self.stats = {
            'companies_analyzed': 0,
            'repositories_analyzed': 0,
            'contributions_generated': 0,
            'reports_created': 0,
            'start_time': datetime.now()
        }
    
    def run_full_analysis(self, companies: List[str] = None, max_repos: int = None) -> Dict[str, Any]:
        """
        Run complete analysis pipeline
        """
        self.console.print(Panel.fit(
            "[bold blue]DevOps Researcher[/bold blue]\n"
            "Analyzing German DevOps companies and generating contributions",
            title="🚀 Starting Analysis"
        ))
        
        try:
            # Load companies
            companies_data = self._load_companies_data()
            if companies:
                companies_data = [c for c in companies_data if c['github_org'] in companies]
            
            # Test GitHub connection
            if not self.github.test_connection():
                self.console.print("[red]❌ GitHub connection failed[/red]")
                return {'success': False, 'error': 'GitHub connection failed'}
            
            # Analyze companies and repositories
            analyses = []
            contribution_plans = []
            
            with Progress() as progress:
                # Create progress tasks
                company_task = progress.add_task(
                    "[cyan]Analyzing companies...", 
                    total=len(companies_data)
                )
                
                for company in companies_data:
                    company_name = company['name']
                    github_org = company['github_org']
                    
                    self.console.print(f"\n[bold]Analyzing {company_name}[/bold] ({github_org})")
                    
                    try:
                        # Get repositories
                        repos = self.github.get_organization_repos(github_org, per_page=50)
                        if max_repos:
                            repos = repos[:max_repos]
                        
                        repo_task = progress.add_task(
                            f"[green]Analyzing repos for {company_name}...", 
                            total=len(repos)
                        )
                        
                        company_analyses = []
                        company_contributions = []
                        
                        for repo in repos:
                            repo_name = repo['name']
                            
                            try:
                                # Analyze repository
                                analysis = self.analyzer.analyze_repository(github_org, repo_name)
                                company_analyses.append(analysis)
                                analyses.append(analysis)
                                
                                # Generate contributions if potential exists
                                if analysis.contribution_potential_score > 30:
                                    contribution_plan = self.contribution_generator.generate_contributions(analysis)
                                    company_contributions.append(contribution_plan)
                                    contribution_plans.append(contribution_plan)
                                    self.stats['contributions_generated'] += len(contribution_plan.items)
                                
                                self.stats['repositories_analyzed'] += 1
                                
                            except Exception as e:
                                logger.error(f"Error analyzing {github_org}/{repo_name}: {e}")
                            
                            progress.advance(repo_task)
                        
                        progress.remove_task(repo_task)
                        
                        # Show company summary
                        self._show_company_summary(company_name, company_analyses, company_contributions)
                        
                        self.stats['companies_analyzed'] += 1
                        
                    except Exception as e:
                        logger.error(f"Error analyzing company {company_name}: {e}")
                    
                    progress.advance(company_task)
            
            # Generate reports
            self.console.print("\n[bold cyan]📊 Generating reports...[/bold cyan]")
            
            report_files = self.report_generator.generate_analysis_report(analyses)
            contribution_report_files = self.report_generator.generate_contribution_report(contribution_plans)
            
            self.stats['reports_created'] = len(report_files) + len(contribution_report_files)
            
            # Show final summary
            self._show_final_summary(analyses, contribution_plans, report_files)
            
            return {
                'success': True,
                'stats': self.stats,
                'analyses': len(analyses),
                'contributions': len(contribution_plans),
                'reports': {**report_files, **contribution_report_files}
            }
            
        except Exception as e:
            logger.error(f"Error in full analysis: {e}")
            self.console.print(f"[red]❌ Analysis failed: {e}[/red]")
            return {'success': False, 'error': str(e)}
    
    def analyze_single_company(self, github_org: str, max_repos: int = 5) -> Dict[str, Any]:
        """
        Analyze a single company
        """
        self.console.print(f"[bold]Analyzing {github_org}[/bold]")
        
        try:
            # Get organization info
            org_info = self.github.get_organization(github_org)
            if not org_info:
                return {'success': False, 'error': f'Organization {github_org} not found'}
            
            # Get repositories
            repos = self.github.get_organization_repos(github_org, per_page=50)
            if max_repos:
                repos = repos[:max_repos]
            
            analyses = []
            contribution_plans = []
            
            with Progress() as progress:
                task = progress.add_task("[green]Analyzing repositories...", total=len(repos))
                
                for repo in repos:
                    repo_name = repo['name']
                    
                    try:
                        # Analyze repository
                        analysis = self.analyzer.analyze_repository(github_org, repo_name)
                        analyses.append(analysis)
                        
                        # Generate contributions if potential exists
                        if analysis.contribution_potential_score > 30:
                            contribution_plan = self.contribution_generator.generate_contributions(analysis)
                            contribution_plans.append(contribution_plan)
                        
                    except Exception as e:
                        logger.error(f"Error analyzing {github_org}/{repo_name}: {e}")
                    
                    progress.advance(task)
            
            # Show results
            self._show_company_summary(github_org, analyses, contribution_plans)
            
            return {
                'success': True,
                'company': github_org,
                'analyses': analyses,
                'contributions': contribution_plans
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {github_org}: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_sample_emails(self, analyses: List[AnalysisResult], 
                              contribution_plans: List[ContributionPlan]) -> None:
        """
        Generate sample outreach emails
        """
        self.console.print("\n[bold cyan]📧 Generating sample emails...[/bold cyan]")
        
        if not analyses or not contribution_plans:
            self.console.print("[yellow]No analyses or contribution plans available for email generation[/yellow]")
            return
        
        # Generate emails for top opportunities
        top_opportunities = sorted(
            zip(analyses, contribution_plans), 
            key=lambda x: x[0].contribution_potential_score, 
            reverse=True
        )[:5]
        
        email_output_dir = Path(settings.output_dir) / "emails"
        email_output_dir.mkdir(exist_ok=True)
        
        for analysis, plan in top_opportunities:
            try:
                # Generate initial contact email
                email = self.email_manager.generate_contribution_email(analysis, plan, 'initial_contact')
                
                # Save to file
                filename = f"{analysis.owner}_{analysis.repo_name}_initial_contact.txt"
                filepath = email_output_dir / filename
                
                with open(filepath, 'w') as f:
                    f.write(f"To: {email.to_email}\n")
                    f.write(f"Subject: {email.subject}\n\n")
                    f.write(email.body)
                
                self.console.print(f"✅ Generated email for {analysis.owner}/{analysis.repo_name}")
                
            except Exception as e:
                logger.error(f"Error generating email for {analysis.owner}/{analysis.repo_name}: {e}")
    
    def _load_companies_data(self) -> List[Dict[str, Any]]:
        """Load companies data from config"""
        config_path = Path(__file__).parent.parent / "config" / "companies.json"
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return data['companies']
    
    def _show_company_summary(self, company_name: str, analyses: List[AnalysisResult], 
                             contributions: List[ContributionPlan]) -> None:
        """Show summary for a single company"""
        if not analyses:
            return
        
        # Calculate averages
        avg_quality = sum(a.overall_quality_score for a in analyses) / len(analyses)
        avg_potential = sum(a.contribution_potential_score for a in analyses) / len(analyses)
        total_contributions = sum(len(c.items) for c in contributions)
        
        # Create summary table
        table = Table(title=f"{company_name} Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Repositories Analyzed", str(len(analyses)))
        table.add_row("Average Quality Score", f"{avg_quality:.1f}")
        table.add_row("Average Contribution Potential", f"{avg_potential:.1f}")
        table.add_row("Contribution Plans", str(len(contributions)))
        table.add_row("Total Contribution Items", str(total_contributions))
        
        self.console.print(table)
        
        # Show top repositories
        if analyses:
            top_repos = sorted(analyses, key=lambda x: x.contribution_potential_score, reverse=True)[:3]
            
            self.console.print(f"\n[bold]Top Opportunities in {company_name}:[/bold]")
            for i, repo in enumerate(top_repos, 1):
                score = repo.contribution_potential_score
                emoji = "🔥" if score > 70 else "⭐" if score > 50 else "💡"
                self.console.print(f"{emoji} {i}. {repo.repo_name} (Score: {score:.1f})")
    
    def _show_final_summary(self, analyses: List[AnalysisResult], 
                           contribution_plans: List[ContributionPlan],
                           report_files: Dict[str, str]) -> None:
        """Show final summary of the entire analysis"""
        
        # Calculate execution time
        execution_time = datetime.now() - self.stats['start_time']
        
        # Create summary panel
        summary_text = f"""
[bold green]✅ Analysis Complete![/bold green]

📊 [bold]Statistics:[/bold]
   • Companies: {self.stats['companies_analyzed']}
   • Repositories: {self.stats['repositories_analyzed']}
   • Contributions Generated: {self.stats['contributions_generated']}
   • Reports Created: {self.stats['reports_created']}
   • Execution Time: {execution_time.total_seconds():.1f}s

📈 [bold]Quality Insights:[/bold]
   • Average Quality Score: {sum(a.overall_quality_score for a in analyses) / len(analyses):.1f}
   • High Potential Repos: {len([a for a in analyses if a.contribution_potential_score > 70])}
   • Ready for Contributions: {len(contribution_plans)}

📁 [bold]Generated Files:[/bold]
"""
        
        for format_type, filepath in report_files.items():
            summary_text += f"   • {format_type.upper()}: {Path(filepath).name}\n"
        
        summary_text += f"""
🎯 [bold]Next Steps:[/bold]
   1. Review generated reports in {settings.reports_dir}/
   2. Check contribution plans in {settings.contributions_dir}/
   3. Use sample emails for outreach
   4. Submit pull requests to selected repositories
"""
        
        self.console.print(Panel(summary_text, title="🚀 DevOps Researcher Results", border_style="green"))
        
        # Show top opportunities
        if analyses:
            top_opportunities = sorted(analyses, key=lambda x: x.contribution_potential_score, reverse=True)[:10]
            
            table = Table(title="🎯 Top Contribution Opportunities")
            table.add_column("Rank", style="cyan", width=6)
            table.add_column("Company", style="magenta")
            table.add_column("Repository", style="green")
            table.add_column("Score", style="yellow", justify="right")
            
            for i, analysis in enumerate(top_opportunities, 1):
                table.add_row(
                    str(i),
                    analysis.owner,
                    analysis.repo_name,
                    f"{analysis.contribution_potential_score:.1f}"
                )
            
            self.console.print(table)