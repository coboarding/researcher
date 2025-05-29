#!/usr/bin/env python3
"""
Contribution Generation Script for DevOps Researcher
Generates specific improvements and pull request materials for repositories.
"""
import sys
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
from rich.prompt import Confirm

from config.settings import settings
from src.github_client import GitHubClient
from src.repo_analyzer import RepositoryAnalyzer
from src.contribution_generator import ContributionGenerator, ContributionPlan
from src.email_templates import EmailTemplateManager

console = Console()
logger = logging.getLogger(__name__)


class ContributionManager:
    """
    Manages the generation and deployment of contributions
    """
    
    def __init__(self):
        self.github = GitHubClient()
        self.analyzer = RepositoryAnalyzer(self.github)
        self.generator = ContributionGenerator()
        self.email_manager = EmailTemplateManager()
        settings.create_directories()
    
    def generate_for_repository(self, owner: str, repo_name: str, 
                               dry_run: bool = True) -> Dict[str, Any]:
        """
        Generate contributions for a specific repository
        """
        console.print(f"[bold cyan]🛠️  Generating contributions for {owner}/{repo_name}[/bold cyan]")
        
        try:
            # Analyze repository first
            console.print("📊 Analyzing repository...")
            analysis = self.analyzer.analyze_repository(owner, repo_name)
            
            # Show analysis summary
            self._display_analysis_summary(analysis)
            
            # Check if contributions are worthwhile
            if analysis.contribution_potential_score < 20:
                console.print("[yellow]⚠️  Low contribution potential. Repository seems well-maintained.[/yellow]")
                if not Confirm.ask("Continue anyway?"):
                    return {'success': False, 'reason': 'Low potential, user declined'}
            
            # Generate contribution plan
            console.print("🔧 Generating contribution plan...")
            plan = self.generator.generate_contributions(analysis)
            
            # Display plan
            self._display_contribution_plan(plan)
            
            if not dry_run:
                # Ask for confirmation
                if not Confirm.ask("Generate these files?"):
                    return {'success': False, 'reason': 'User declined'}
                
                # Save contribution files
                self._save_contribution_files(plan)
                
                # Generate PR description
                pr_description = self.generator.create_pr_description(plan)
                self._save_pr_materials(plan, pr_description)
                
                # Generate outreach email
                email = self.email_manager.generate_contribution_email(
                    analysis, plan, 'maintainer_contact'
                )
                self._save_email(email, plan)
            
            return {
                'success': True,
                'analysis': analysis,
                'plan': plan,
                'dry_run': dry_run
            }
            
        except Exception as e:
            logger.error(f"Error generating contributions: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_batch_contributions(self, repositories: List[Dict[str, str]], 
                                   min_score: float = 50.0,
                                   max_contributions: int = 10,
                                   dry_run: bool = True) -> Dict[str, Any]:
        """
        Generate contributions for multiple repositories
        """
        console.print(f"[bold cyan]🚀 Batch generating contributions for {len(repositories)} repositories[/bold cyan]")
        
        successful_plans = []
        failed_repos = []
        
        with Progress() as progress:
            task = progress.add_task("[green]Processing repositories...", total=len(repositories))
            
            for repo_info in repositories:
                owner = repo_info['owner']
                repo_name = repo_info['repo']
                
                try:
                    # Analyze repository
                    analysis = self.analyzer.analyze_repository(owner, repo_name)
                    
                    # Check if it meets criteria
                    if analysis.contribution_potential_score >= min_score:
                        # Generate contributions
                        plan = self.generator.generate_contributions(analysis)
                        successful_plans.append((analysis, plan))
                        
                        console.print(f"✅ {owner}/{repo_name} - Score: {analysis.contribution_potential_score:.1f}")
                        
                        if len(successful_plans) >= max_contributions:
                            console.print(f"[yellow]⚠️  Reached maximum contributions limit ({max_contributions})[/yellow]")
                            break
                    else:
                        console.print(f"⏭️  {owner}/{repo_name} - Score too low: {analysis.contribution_potential_score:.1f}")
                
                except Exception as e:
                    logger.error(f"Error processing {owner}/{repo_name}: {e}")
                    failed_repos.append({'owner': owner, 'repo': repo_name, 'error': str(e)})
                
                progress.advance(task)
        
        # Display batch summary
        self._display_batch_summary(successful_plans, failed_repos)
        
        if not dry_run and successful_plans:
            if Confirm.ask(f"Generate files for {len(successful_plans)} repositories?"):
                self._save_batch_contributions(successful_plans)
        
        return {
            'success': True,
            'successful_plans': successful_plans,
            'failed_repos': failed_repos,
            'total_processed': len(repositories)
        }
    
    def create_pr_ready_contributions(self, owner: str, repo_name: str,
                                    fork_repo: bool = False) -> Dict[str, Any]:
        """
        Create PR-ready contributions with Git setup
        """
        console.print(f"[bold cyan]🔀 Creating PR-ready contributions for {owner}/{repo_name}[/bold cyan]")
        
        # This would typically involve:
        # 1. Fork the repository (if enabled)
        # 2. Clone locally
        # 3. Create feature branch
        # 4. Apply changes
        # 5. Commit and push
        # 6. Create PR via API
        
        console.print("[yellow]⚠️  PR automation not implemented in this version[/yellow]")
        console.print("📋 To create PR manually:")
        console.print("1. Fork the repository")
        console.print("2. Clone your fork")
        console.print("3. Create feature branch: git checkout -b feature/devops-improvements")
        console.print("4. Copy generated files to repository")
        console.print("5. Commit and push changes")
        console.print("6. Create PR on GitHub")
        
        return {
            'success': True,
            'manual_steps_required': True,
            'repository': f"{owner}/{repo_name}"
        }
    
    def _display_analysis_summary(self, analysis) -> None:
        """Display repository analysis summary"""
        
        # Basic info
        info_text = f"""
[bold]Repository:[/bold] {analysis.owner}/{analysis.repo_name}
[bold]Language:[/bold] {analysis.language or 'Unknown'}
[bold]Description:[/bold] {analysis.description or 'No description'}
[bold]Stars:[/bold] {analysis.stars} | [bold]Forks:[/bold] {analysis.forks}
[bold]Last Updated:[/bold] {analysis.last_updated.strftime('%Y-%m-%d') if analysis.last_updated else 'Unknown'}
"""
        
        console.print(Panel(info_text, title="📊 Repository Analysis", border_style="blue"))
        
        # Scores
        scores_table = Table(title="Quality Scores")
        scores_table.add_column("Metric", style="cyan")
        scores_table.add_column("Score", style="green", justify="right")
        scores_table.add_column("Status", style="yellow")
        
        scores_table.add_row(
            "Overall Quality", 
            f"{analysis.overall_quality_score:.1f}/100",
            "🟢 Good" if analysis.overall_quality_score >= 70 else "🟡 Fair" if analysis.overall_quality_score >= 40 else "🔴 Poor"
        )
        scores_table.add_row(
            "Contribution Potential", 
            f"{analysis.contribution_potential_score:.1f}/100",
            "🔥 High" if analysis.contribution_potential_score >= 70 else "⭐ Medium" if analysis.contribution_potential_score >= 40 else "💡 Low"
        )
        
        console.print(scores_table)
        
        # Missing features
        if analysis.contribution_opportunities:
            console.print("\n[bold]🎯 Identified Opportunities:[/bold]")
            for i, opportunity in enumerate(analysis.contribution_opportunities, 1):
                console.print(f"  {i}. {opportunity}")
    
    def _display_contribution_plan(self, plan: ContributionPlan) -> None:
        """Display contribution plan details"""
        
        console.print(f"\n[bold green]📋 Contribution Plan for {plan.owner}/{plan.repo_name}[/bold green]")
        console.print(f"[bold]Estimated Time:[/bold] {plan.estimated_time}")
        console.print(f"[bold]Total Items:[/bold] {len(plan.items)}")
        
        # Plan summary
        console.print(f"\n[bold]Summary:[/bold]\n{plan.summary}")
        
        # Items table
        items_table = Table(title="Contribution Items")
        items_table.add_column("Priority", width=8)
        items_table.add_column("File", style="cyan")
        items_table.add_column("Description", style="green")
        items_table.add_column("Impact", style="yellow")
        
        for item in plan.items:
            priority_emoji = "🔴" if item.priority == 1 else "🟡" if item.priority == 2 else "🔵"
            items_table.add_row(
                f"{priority_emoji} {item.priority}",
                item.file_path,
                item.description,
                item.estimated_impact
            )
        
        console.print(items_table)
    
    def _display_batch_summary(self, successful_plans: List, failed_repos: List) -> None:
        """Display summary of batch processing"""
        
        console.print(f"\n[bold green]📊 Batch Processing Summary[/bold green]")
        console.print(f"✅ Successful: {len(successful_plans)}")
        console.print(f"❌ Failed: {len(failed_repos)}")
        
        if successful_plans:
            console.print("\n[bold]🎯 Top Opportunities:[/bold]")
            
            # Sort by potential score
            sorted_plans = sorted(successful_plans, key=lambda x: x[0].contribution_potential_score, reverse=True)
            
            for i, (analysis, plan) in enumerate(sorted_plans[:10], 1):
                score = analysis.contribution_potential_score
                emoji = "🔥" if score > 80 else "⭐" if score > 60 else "💡"
                console.print(f"  {emoji} {i}. {analysis.owner}/{analysis.repo_name} - Score: {score:.1f} ({len(plan.items)} items)")
        
        if failed_repos:
            console.print("\n[bold red]❌ Failed Repositories:[/bold red]")
            for repo in failed_repos:
                console.print(f"  • {repo['owner']}/{repo['repo']}: {repo['error']}")
    
    def _save_contribution_files(self, plan: ContributionPlan) -> None:
        """Save individual contribution files"""
        repo_dir = Path(settings.contributions_dir) / f"{plan.owner}_{plan.repo_name}"
        repo_dir.mkdir(parents=True, exist_ok=True)
        
        console.print(f"💾 Saving files to {repo_dir}")
        
        for item in plan.items:
            file_path = repo_dir / item.file_path.replace('/', '_')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(item.content)
            
            console.print(f"  ✅ {item.file_path}")
    
    def _save_pr_materials(self, plan: ContributionPlan, pr_description: str) -> None:
        """Save PR description and related materials"""
        repo_dir = Path(settings.contributions_dir) / f"{plan.owner}_{plan.repo_name}"
        
        # PR description
        pr_file = repo_dir / "PULL_REQUEST_DESCRIPTION.md"
        with open(pr_file, 'w') as f:
            f.write(pr_description)
        
        # Commit messages
        commit_file = repo_dir / "COMMIT_MESSAGES.txt"
        with open(commit_file, 'w') as f:
            f.write("Suggested commit messages:\n\n")
            for item in plan.items:
                commit_msg = f"feat: {item.description}\n\n"
                commit_msg += f"- Add {item.file_path}\n"
                commit_msg += f"- {item.description}\n"
                commit_msg += f"- Priority: {item.priority}, Impact: {item.estimated_impact}\n\n"
                f.write(commit_msg)
        
        console.print(f"  ✅ PR materials saved")
    
    def _save_email(self, email, plan: ContributionPlan) -> None:
        """Save outreach email"""
        repo_dir = Path(settings.contributions_dir) / f"{plan.owner}_{plan.repo_name}"
        
        email_file = repo_dir / "OUTREACH_EMAIL.txt"
        with open(email_file, 'w') as f:
            f.write(f"To: {email.to_email}\n")
            f.write(f"Subject: {email.subject}\n\n")
            f.write(email.body)
        
        console.print(f"  ✅ Outreach email saved")
    
    def _save_batch_contributions(self, successful_plans: List) -> None:
        """Save all batch contributions"""
        console.print("💾 Saving batch contributions...")
        
        for analysis, plan in successful_plans:
            try:
                self._save_contribution_files(plan)
                
                pr_description = self.generator.create_pr_description(plan)
                self._save_pr_materials(plan, pr_description)
                
                email = self.email_manager.generate_contribution_email(
                    analysis, plan, 'maintainer_contact'
                )
                self._save_email(email, plan)
                
            except Exception as e:
                logger.error(f"Error saving {plan.owner}/{plan.repo_name}: {e}")
        
        console.print(f"✅ Saved contributions for {len(successful_plans)} repositories")


def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate contributions for repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate for single repository
  python scripts/generate_contributions.py single zalando team-api

  # Generate for multiple repositories (dry run)
  python scripts/generate_contributions.py batch --repos zalando/team-api sap/ui5-webcomponents

  # Generate with specific criteria
  python scripts/generate_contributions.py batch --repos-file repos.txt --min-score 60

  # Create PR-ready contributions
  python scripts/generate_contributions.py pr zalando team-api --fork
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Generation commands')
    
    # Single repository
    single_parser = subparsers.add_parser('single', help='Generate for single repository')
    single_parser.add_argument('owner', help='Repository owner')
    single_parser.add_argument('repo', help='Repository name')
    single_parser.add_argument('--dry-run', action='store_true', help='Preview only, do not generate files')
    
    # Batch generation
    batch_parser = subparsers.add_parser('batch', help='Generate for multiple repositories')
    repo_group = batch_parser.add_mutually_exclusive_group(required=True)
    repo_group.add_argument('--repos', nargs='+', help='Repository in format owner/repo')
    repo_group.add_argument('--repos-file', help='File containing list of repositories')
    batch_parser.add_argument('--min-score', type=float, default=50.0, help='Minimum contribution score')
    batch_parser.add_argument('--max-contributions', type=int, default=10, help='Maximum contributions to generate')
    batch_parser.add_argument('--dry-run', action='store_true', help='Preview only')
    
    # PR creation
    pr_parser = subparsers.add_parser('pr', help='Create PR-ready contributions')
    pr_parser.add_argument('owner', help='Repository owner')
    pr_parser.add_argument('repo', help='Repository name')
    pr_parser.add_argument('--fork', action='store_true', help='Automatically fork repository')
    
    # From analysis results
    analysis_parser = subparsers.add_parser('from-analysis', help='Generate from existing analysis')
    analysis_parser.add_argument('analysis_file', help='JSON file with analysis results')
    analysis_parser.add_argument('--min-score', type=float, default=50.0, help='Minimum score')
    
    return parser


def parse_repositories(repos_arg: Optional[List[str]] = None, 
                      repos_file: Optional[str] = None) -> List[Dict[str, str]]:
    """Parse repository arguments into structured format"""
    repositories = []
    
    if repos_arg:
        for repo_str in repos_arg:
            if '/' in repo_str:
                owner, repo = repo_str.split('/', 1)
                repositories.append({'owner': owner, 'repo': repo})
            else:
                console.print(f"[yellow]⚠️  Invalid format: {repo_str} (expected: owner/repo)[/yellow]")
    
    if repos_file:
        try:
            with open(repos_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '/' in line:
                            owner, repo = line.split('/', 1)
                            repositories.append({'owner': owner, 'repo': repo})
        except FileNotFoundError:
            console.print(f"[red]❌ File not found: {repos_file}[/red]")
    
    return repositories


def main():
    """Main entry point"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = ContributionManager()
    
    try:
        if args.command == 'single':
            result = manager.generate_for_repository(
                args.owner, 
                args.repo, 
                dry_run=getattr(args, 'dry_run', True)
            )
            
        elif args.command == 'batch':
            repositories = parse_repositories(
                getattr(args, 'repos', None),
                getattr(args, 'repos_file', None)
            )
            
            if not repositories:
                console.print("[red]❌ No valid repositories found[/red]")
                return 1
            
            result = manager.generate_batch_contributions(
                repositories,
                min_score=args.min_score,
                max_contributions=args.max_contributions,
                dry_run=getattr(args, 'dry_run', True)
            )
            
        elif args.command == 'pr':
            result = manager.create_pr_ready_contributions(
                args.owner,
                args.repo,
                fork_repo=getattr(args, 'fork', False)
            )
            
        elif args.command == 'from-analysis':
            console.print("[yellow]⚠️  Analysis file processing not implemented[/yellow]")
            return 1
        
        if result.get('success'):
            console.print("\n[bold green]✅ Contribution generation completed![/bold green]")
            
            if result.get('dry_run'):
                console.print("[yellow]💡 This was a dry run. Use --no-dry-run to generate actual files.[/yellow]")
            else:
                console.print(f"📁 Check generated files in: {settings.contributions_dir}")
        else:
            console.print(f"\n[bold red]❌ Generation failed: {result.get('error', result.get('reason', 'Unknown error'))}[/bold red]")
            return 1
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Generation interrupted[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]💥 Error: {e}[/bold red]")
        logger.error(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())