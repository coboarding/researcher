"""
Report Generator for DevOps Researcher
Generates comprehensive reports in various formats (CSV, HTML, PDF, JSON).
"""
import csv
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from jinja2 import Template

from src.repo_analyzer import AnalysisResult
from src.contribution_generator import ContributionPlan
from config.settings import settings, REPORT_CONFIG

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive reports about companies, repositories, and contributions
    """

    def __init__(self):
        self.output_dir = Path(settings.reports_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = REPORT_CONFIG

        # Set up matplotlib
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['figure.dpi'] = 100

    def generate_analysis_report(self, analyses: List[AnalysisResult],
                               format_types: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generate comprehensive analysis report in multiple formats
        """
        if format_types is None:
            format_types = self.config['formats']

        logger.info(f"Generating analysis report for {len(analyses)} repositories")

        # Prepare data
        report_data = self._prepare_analysis_data(analyses)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        generated_files = {}

        # Generate different formats
        for format_type in format_types:
            try:
                if format_type == 'csv':
                    file_path = self._generate_csv_report(report_data, timestamp)
                elif format_type == 'html':
                    file_path = self._generate_html_report(report_data, analyses, timestamp)
                elif format_type == 'json':
                    file_path = self._generate_json_report(report_data, timestamp)
                elif format_type == 'pdf':
                    file_path = self._generate_pdf_report(report_data, analyses, timestamp)
                else:
                    logger.warning(f"Unknown format: {format_type}")
                    continue

                generated_files[format_type] = str(file_path)
                logger.info(f"Generated {format_type.upper()} report: {file_path}")

            except Exception as e:
                logger.error(f"Error generating {format_type} report: {e}")

        return generated_files

    def generate_contribution_report(self, plans: List[ContributionPlan]) -> Dict[str, str]:
        """Generate report about contribution plans"""
        logger.info(f"Generating contribution report for {len(plans)} plans")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        generated_files = {}

        # CSV report
        csv_path = self._generate_contribution_csv(plans, timestamp)
        generated_files['csv'] = str(csv_path)

        # HTML dashboard
        html_path = self._generate_contribution_html(plans, timestamp)
        generated_files['html'] = str(html_path)

        return generated_files

    def _prepare_analysis_data(self, analyses: List[AnalysisResult]) -> pd.DataFrame:
        """Prepare analysis data for reporting"""
        data = []

        for analysis in analyses:
            row = {
                'company': analysis.owner,
                'repository': analysis.repo_name,
                'language': analysis.language or 'Unknown',
                'stars': analysis.stars,
                'forks': analysis.forks,
                'open_issues': analysis.open_issues,
                'last_updated': analysis.last_updated.strftime('%Y-%m-%d') if analysis.last_updated else 'Unknown',
                'has_readme': analysis.has_readme,
                'readme_quality_score': round(analysis.readme_quality_score, 2),
                'has_makefile': analysis.has_makefile,
                'makefile_quality_score': round(analysis.makefile_quality_score, 2),
                'has_tests': analysis.has_tests,
                'test_framework': analysis.test_framework or 'None',
                'has_ci_cd': analysis.has_ci_cd,
                'ci_cd_platform': analysis.ci_cd_platform or 'None',
                'has_docker': analysis.has_docker,
                'has_linting': analysis.has_linting,
                'has_formatting': analysis.has_formatting,
                'overall_quality_score': round(analysis.overall_quality_score, 2),
                'contribution_potential_score': round(analysis.contribution_potential_score, 2),
                'help_wanted_issues': len(analysis.help_wanted_issues),
                'good_first_issues': len(analysis.good_first_issues),
                'contribution_opportunities': len(analysis.contribution_opportunities),
                'readme_issues_count': len(analysis.readme_issues),
                'makefile_issues_count': len(analysis.makefile_issues),
                'testing_issues_count': len(analysis.testing_issues),
                'ci_cd_issues_count': len(analysis.ci_cd_issues),
                'docker_issues_count': len(analysis.docker_issues),
                'code_quality_issues_count': len(analysis.code_quality_issues)
            }
            data.append(row)

        return pd.DataFrame(data)

    def _generate_csv_report(self, data: pd.DataFrame, timestamp: str) -> Path:
        """Generate CSV report"""
        file_path = self.output_dir / f"analysis_report_{timestamp}.csv"
        data.to_csv(file_path, index=False)
        return file_path

    def _generate_json_report(self, data: pd.DataFrame, timestamp: str) -> Path:
        """Generate JSON report"""
        file_path = self.output_dir / f"analysis_report_{timestamp}.json"

        # Convert DataFrame to JSON-serializable format
        json_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_repositories': len(data),
                'total_companies': data['company'].nunique(),
                'report_version': '1.0'
            },
            'summary': self._generate_summary_stats(data),
            'repositories': data.to_dict(orient='records')
        }

        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)

        return file_path

    def _generate_html_report(self, data: pd.DataFrame, analyses: List[AnalysisResult],
                             timestamp: str) -> Path:
        """Generate comprehensive HTML report with visualizations"""
        file_path = self.output_dir / f"analysis_report_{timestamp}.html"

        # Generate visualizations
        charts = self._generate_charts(data)

        # Prepare template data
        template_data = {
            'title': 'DevOps Researcher - Analysis Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': self._generate_summary_stats(data),
            'charts': charts,
            'top_repositories': self._get_top_repositories(data),
            'recommendations': self._generate_recommendations(data),
            'data_table': data.to_html(classes='table table-striped table-hover',
                                     table_id='analysis-table', escape=False)
        }

        # Load and render template
        html_template = self._get_html_template()
        rendered_html = html_template.render(**template_data)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)

        return file_path

    def _generate_pdf_report(self, data: pd.DataFrame, analyses: List[AnalysisResult],
                            timestamp: str) -> Path:
        """Generate PDF report"""
        try:
            from fpdf import FPDF

            file_path = self.output_dir / f"analysis_report_{timestamp}.pdf"

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)

            # Title
            pdf.cell(0, 10, 'DevOps Researcher - Analysis Report', 0, 1, 'C')
            pdf.ln(10)

            # Summary
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Summary', 0, 1)
            pdf.set_font('Arial', '', 10)

            summary = self._generate_summary_stats(data)
            for key, value in summary.items():
                pdf.cell(0, 6, f'{key}: {value}', 0, 1)

            pdf.ln(10)

            # Top repositories
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Top Repositories by Quality Score', 0, 1)
            pdf.set_font('Arial', '', 9)

            top_repos = data.nlargest(10, 'overall_quality_score')
            for _, repo in top_repos.iterrows():
                pdf.cell(0, 5, f"{repo['company']}/{repo['repository']} - Score: {repo['overall_quality_score']}", 0, 1)

            pdf.output(str(file_path))
            return file_path

        except ImportError:
            logger.warning("fpdf2 not available, skipping PDF generation")
            return None

    def _generate_charts(self, data: pd.DataFrame) -> Dict[str, str]:
        """Generate interactive charts using Plotly"""
        charts = {}

        # Company distribution
        if self.config['charts']['company_distribution']:
            fig = px.bar(
                data.groupby('company').size().reset_index(name='count'),
                x='company', y='count',
                title='Repositories per Company',
                labels={'count': 'Number of Repositories', 'company': 'Company'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            charts['company_distribution'] = fig.to_html(include_plotlyjs='cdn')

        # Quality metrics distribution
        if self.config['charts']['repo_quality_metrics']:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=['Overall Quality Score', 'Contribution Potential',
                               'Stars Distribution', 'Language Distribution']
            )

            # Quality score histogram
            fig.add_trace(
                go.Histogram(x=data['overall_quality_score'], name='Quality Score'),
                row=1, col=1
            )

            # Contribution potential histogram
            fig.add_trace(
                go.Histogram(x=data['contribution_potential_score'], name='Contribution Potential'),
                row=1, col=2
            )

            # Stars scatter plot
            fig.add_trace(
                go.Scatter(x=data['stars'], y=data['overall_quality_score'],
                          mode='markers', name='Stars vs Quality'),
                row=2, col=1
            )

            # Language pie chart
            lang_counts = data['language'].value_counts().head(8)
            fig.add_trace(
                go.Pie(labels=lang_counts.index, values=lang_counts.values, name='Languages'),
                row=2, col=2
            )

            fig.update_layout(height=800, showlegend=False)
            charts['quality_metrics'] = fig.to_html(include_plotlyjs='cdn')

        # Contribution opportunities
        if self.config['charts']['contribution_opportunities']:
            opportunity_data = []
            for _, row in data.iterrows():
                opportunities = {
                    'Missing README': not row['has_readme'],
                    'Missing Makefile': not row['has_makefile'],
                    'Missing Tests': not row['has_tests'],
                    'Missing CI/CD': not row['has_ci_cd'],
                    'Missing Docker': not row['has_docker'],
                    'Missing Linting': not row['has_linting']
                }
                opportunity_data.append(opportunities)

            opp_df = pd.DataFrame(opportunity_data)
            opp_counts = opp_df.sum()

            fig = px.bar(
                x=opp_counts.index, y=opp_counts.values,
                title='Contribution Opportunities Across All Repositories',
                labels={'x': 'Improvement Type', 'y': 'Number of Repositories'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            charts['contribution_opportunities'] = fig.to_html(include_plotlyjs='cdn')

        return charts

    def _generate_summary_stats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics"""
        return {
            'Total Repositories': len(data),
            'Total Companies': data['company'].nunique(),
            'Average Quality Score': round(data['overall_quality_score'].mean(), 2),
            'Average Contribution Potential': round(data['contribution_potential_score'].mean(), 2),
            'Repositories with README': data['has_readme'].sum(),
            'Repositories with Makefile': data['has_makefile'].sum(),
            'Repositories with Tests': data['has_tests'].sum(),
            'Repositories with CI/CD': data['has_ci_cd'].sum(),
            'Repositories with Docker': data['has_docker'].sum(),
            'Most Common Language': data['language'].mode().iloc[0] if not data['language'].mode().empty else 'Unknown',
            'Total Stars': data['stars'].sum(),
            'Total Forks': data['forks'].sum(),
            'Total Open Issues': data['open_issues'].sum(),
            'Help Wanted Issues': data['help_wanted_issues'].sum(),
            'Good First Issues': data['good_first_issues'].sum()
        }

    def _get_top_repositories(self, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Get top repositories by different metrics"""
        return {
            'by_quality': data.nlargest(10, 'overall_quality_score')[
                ['company', 'repository', 'overall_quality_score', 'language', 'stars']
            ],
            'by_contribution_potential': data.nlargest(10, 'contribution_potential_score')[
                ['company', 'repository', 'contribution_potential_score', 'contribution_opportunities']
            ],
            'by_stars': data.nlargest(10, 'stars')[
                ['company', 'repository', 'stars', 'language', 'overall_quality_score']
            ],
            'most_opportunities': data.nlargest(10, 'contribution_opportunities')[
                ['company', 'repository', 'contribution_opportunities', 'contribution_potential_score']
            ]
        }

    def _generate_recommendations(self, data: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        # Quality recommendations
        low_quality_repos = data[data['overall_quality_score'] < 50]
        if len(low_quality_repos) > 0:
            recommendations.append(
                f"Focus on {len(low_quality_repos)} repositories with quality scores below 50. "
                f"These offer the highest impact improvement opportunities."
            )

        # Missing documentation
        no_readme = data[~data['has_readme']]
        if len(no_readme) > 0:
            recommendations.append(
                f"{len(no_readme)} repositories lack README files. "
                f"Adding documentation would significantly improve their accessibility."
            )

        # Missing build systems
        no_makefile = data[~data['has_makefile']]
        if len(no_makefile) > 0:
            recommendations.append(
                f"{len(no_makefile)} repositories would benefit from standardized build scripts (Makefile)."
            )

        # Missing CI/CD
        no_ci_cd = data[~data['has_ci_cd']]
        if len(no_ci_cd) > 0:
            recommendations.append(
                f"{len(no_ci_cd)} repositories lack CI/CD pipelines. "
                f"Adding automated testing would improve code quality."
            )

        # High potential repos
        high_potential = data[data['contribution_potential_score'] > 70]
        if len(high_potential) > 0:
            top_targets = high_potential.nlargest(5, 'contribution_potential_score')
            repo_list = [f"{row['company']}/{row['repository']}" for _, row in top_targets.iterrows()]
            recommendations.append(
                f"Priority targets for contributions: {', '.join(repo_list)}"
            )

        return recommendations

    def _generate_contribution_csv(self, plans: List[ContributionPlan], timestamp: str) -> Path:
        """Generate CSV report for contribution plans"""
        file_path = self.output_dir / f"contribution_plans_{timestamp}.csv"

        data = []
        for plan in plans:
            for item in plan.items:
                data.append({
                    'company': plan.owner,
                    'repository': plan.repo_name,
                    'file_path': item.file_path,
                    'description': item.description,
                    'priority': item.priority,
                    'estimated_impact': item.estimated_impact,
                    'plan_summary': plan.summary,
                    'estimated_time': plan.estimated_time,
                    'created_at': plan.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        return file_path

    def _generate_contribution_html(self, plans: List[ContributionPlan], timestamp: str) -> Path:
        """Generate HTML dashboard for contribution plans"""
        file_path = self.output_dir / f"contribution_dashboard_{timestamp}.html"

        # Prepare data for template
        template_data = {
            'title': 'DevOps Researcher - Contribution Plans',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_plans': len(plans),
            'total_contributions': sum(len(plan.items) for plan in plans),
            'plans': plans
        }

        # Simple HTML template for contribution dashboard
        html_content = self._get_contribution_dashboard_template().render(**template_data)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return file_path

    def _get_html_template(self) -> Template:
        """Get main HTML report template"""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/1.11.5/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <style>
        .chart-container { margin: 20px 0; }
        .summary-card { margin-bottom: 20px; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-12">
                <h1 class="mt-4 mb-4">{{ title }}</h1>
                <p class="text-muted">Generated on {{ generated_at }}</p>
            </div>
        </div>
        
        <!-- Summary Cards -->
        <div class="row">
            {% for key, value in summary.items() %}
            <div class="col-lg-3 col-md-4 col-sm-6 mb-3">
                <div class="card summary-card">
                    <div class="card-body text-center">
                        <div class="metric-value">{{ value }}</div>
                        <div class="text-muted">{{ key }}</div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <!-- Charts -->
        {% for chart_name, chart_html in charts.items() %}
        <div class="row chart-container">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        {{ chart_html|safe }}
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
        
        <!-- Recommendations -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Recommendations</h5>
                    </div>
                    <div class="card-body">
                        <ul>
                        {% for recommendation in recommendations %}
                            <li>{{ recommendation }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Top Repositories -->
        {% for category, repos in top_repositories.items() %}
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Top Repositories {{ category.replace('_', ' ').title() }}</h5>
                    </div>
                    <div class="card-body">
                        {{ repos.to_html(classes='table table-striped', escape=False)|safe }}
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
        
        <!-- Full Data Table -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Complete Analysis Data</h5>
                    </div>
                    <div class="card-body">
                        {{ data_table|safe }}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.11.5/js/dataTables.bootstrap5.min.js"></script>
    <script>
        $(document).ready(function() {
            $('#analysis-table').DataTable({
                "pageLength": 25,
                "order": [[ 17, "desc" ]], // Sort by quality score
                "columnDefs": [
                    { "type": "num", "targets": [4, 5, 6, 8, 10, 17, 18] }
                ]
            });
        });
    </script>
</body>
</html>
        """
        return Template(template_str)

    def _get_contribution_dashboard_template(self) -> Template:
        """Get contribution dashboard template"""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container-fluid">
        <h1 class="mt-4 mb-4">{{ title }}</h1>
        <p class="text-muted">Generated on {{ generated_at }}</p>
        
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h2 class="text-primary">{{ total_plans }}</h2>
                        <p>Total Contribution Plans</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h2 class="text-success">{{ total_contributions }}</h2>
                        <p>Total Contribution Items</p>
                    </div>
                </div>
            </div>
        </div>
        
        {% for plan in plans %}
        <div class="card mb-4">
            <div class="card-header">
                <h5>{{ plan.owner }}/{{ plan.repo_name }}</h5>
                <small class="text-muted">{{ plan.estimated_time }} • {{ plan.created_at.strftime('%Y-%m-%d') }}</small>
            </div>
            <div class="card-body">
                <p>{{ plan.summary }}</p>
                
                <h6>Contribution Items:</h6>
                <div class="row">
                    {% for item in plan.items %}
                    <div class="col-md-6 mb-2">
                        <div class="border p-2 rounded">
                            <strong>{{ item.file_path }}</strong>
                            <p class="small mb-1">{{ item.description }}</p>
                            <span class="badge bg-{% if item.priority == 1 %}danger{% elif item.priority == 2 %}warning{% else %}info{% endif %}">
                                Priority {{ item.priority }}
                            </span>
                            <span class="badge bg-secondary">{{ item.estimated_impact }}</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
        """
        return Template(template_str)