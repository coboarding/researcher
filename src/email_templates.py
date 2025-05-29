"""
Email Templates for DevOps Researcher
Generates personalized outreach messages for companies and maintainers.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from jinja2 import Template

from src.repo_analyzer import AnalysisResult
from src.contribution_generator import ContributionPlan
from config.settings import EMAIL_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class EmailTemplate:
    """Email template configuration"""
    name: str
    subject_template: str
    body_template: str
    tone: str  # professional, friendly, casual
    max_length: int
    use_html: bool = False


@dataclass
class PersonalizedEmail:
    """Personalized email ready to send"""
    to_email: str
    to_name: str
    subject: str
    body: str
    template_name: str
    company: str
    repository: str
    generated_at: datetime


class EmailTemplateManager:
    """
    Manages email templates and generates personalized outreach messages
    """

    def __init__(self):
        self.config = EMAIL_CONFIG
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, EmailTemplate]:
        """Load all email templates"""
        templates = {}

        # Initial contact template
        templates['initial_contact'] = EmailTemplate(
            name='initial_contact',
            subject_template="Open Source Contribution - {{ repo_name }}",
            body_template=self._get_initial_contact_template(),
            tone='professional',
            max_length=200,
            use_html=False
        )

        # Follow-up template
        templates['follow_up'] = EmailTemplate(
            name='follow_up',
            subject_template="Re: Open Source Contribution - {{ repo_name }}",
            body_template=self._get_follow_up_template(),
            tone='friendly',
            max_length=150,
            use_html=False
        )

        # Job inquiry template
        templates['job_inquiry'] = EmailTemplate(
            name='job_inquiry',
            subject_template="DevOps Engineer Position - Portfolio Review",
            body_template=self._get_job_inquiry_template(),
            tone='professional',
            max_length=250,
            use_html=False
        )

        # Maintainer contact template
        templates['maintainer_contact'] = EmailTemplate(
            name='maintainer_contact',
            subject_template="Contribution Proposal for {{ repo_name }}",
            body_template=self._get_maintainer_contact_template(),
            tone='collaborative',
            max_length=180,
            use_html=False
        )

        # LinkedIn message template
        templates['linkedin_message'] = EmailTemplate(
            name='linkedin_message',
            subject_template="DevOps Collaboration Opportunity",
            body_template=self._get_linkedin_template(),
            tone='professional',
            max_length=300,
            use_html=False
        )

        return templates

    def generate_personalized_email(self, template_name: str, context: Dict[str, Any]) -> PersonalizedEmail:
        """Generate a personalized email from template and context"""

        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")

        template = self.templates[template_name]

        # Render subject
        subject_tmpl = Template(template.subject_template)
        subject = subject_tmpl.render(**context)

        # Render body
        body_tmpl = Template(template.body_template)
        body = body_tmpl.render(**context)

        # Ensure length limits
        if len(body) > template.max_length and template.max_length > 0:
            body = self._truncate_message(body, template.max_length)

        return PersonalizedEmail(
            to_email=context.get('to_email', ''),
            to_name=context.get('to_name', ''),
            subject=subject,
            body=body,
            template_name=template_name,
            company=context.get('company', ''),
            repository=context.get('repo_name', ''),
            generated_at=datetime.now()
        )

    def generate_contribution_email(self, analysis: AnalysisResult,
                                   contribution_plan: ContributionPlan,
                                   template_name: str = 'initial_contact') -> PersonalizedEmail:
        """Generate email for a specific contribution opportunity"""

        context = self._build_contribution_context(analysis, contribution_plan)
        return self.generate_personalized_email(template_name, context)

    def generate_job_inquiry_email(self, company_info: Dict[str, Any],
                                  portfolio_summary: Dict[str, Any]) -> PersonalizedEmail:
        """Generate job inquiry email"""

        context = self._build_job_inquiry_context(company_info, portfolio_summary)
        return self.generate_personalized_email('job_inquiry', context)

    def _build_contribution_context(self, analysis: AnalysisResult,
                                   contribution_plan: ContributionPlan) -> Dict[str, Any]:
        """Build context for contribution-related emails"""

        # Summarize contributions
        contribution_summary = self._summarize_contributions(contribution_plan)

        # Get recent activity
        recent_activity = self._get_recent_activity_summary(analysis)

        context = {
            'company': analysis.owner,
            'repo_name': analysis.repo_name,
            'repo_description': analysis.description,
            'repo_language': analysis.language or 'the project',
            'repo_stars': analysis.stars,
            'contribution_count': len(contribution_plan.items),
            'contribution_summary': contribution_summary,
            'estimated_time': contribution_plan.estimated_time,
            'quality_score': analysis.overall_quality_score,
            'recent_activity': recent_activity,
            'help_wanted_count': len(analysis.help_wanted_issues),
            'github_profile': 'https://github.com/your-username',  # TODO: Make configurable
            'your_name': 'Your Name',  # TODO: Make configurable
            'your_email': 'your.email@example.com',  # TODO: Make configurable
            'to_email': f'team@{analysis.owner.lower()}.com',  # Estimated
            'to_name': f'{analysis.owner} Team'
        }

        return context

    def _build_job_inquiry_context(self, company_info: Dict[str, Any],
                                  portfolio_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Build context for job inquiry emails"""

        context = {
            'company': company_info.get('name', ''),
            'company_tech_stack': ', '.join(company_info.get('tech_stack', [])),
            'your_name': 'Your Name',  # TODO: Make configurable
            'your_email': 'your.email@example.com',  # TODO: Make configurable
            'your_experience_years': portfolio_summary.get('experience_years', '3+'),
            'contribution_count': portfolio_summary.get('total_contributions', 0),
            'github_profile': 'https://github.com/your-username',  # TODO: Make configurable
            'linkedin_profile': 'https://linkedin.com/in/your-profile',  # TODO: Make configurable
            'portfolio_highlights': portfolio_summary.get('highlights', []),
            'preferred_work_mode': 'part-time (~20h/week)',  # TODO: Make configurable
            'to_email': company_info.get('hr_email', f'careers@{company_info.get("name", "").lower()}.com'),
            'to_name': 'Hiring Team'
        }

        return context

    def _summarize_contributions(self, plan: ContributionPlan) -> str:
        """Create a brief summary of planned contributions"""
        if not plan.items:
            return "general improvements"

        improvements = []
        for item in plan.items[:3]:  # Top 3 items
            if 'README' in item.file_path:
                improvements.append('documentation')
            elif 'Makefile' in item.file_path:
                improvements.append('build automation')
            elif 'test' in item.file_path.lower():
                improvements.append('testing setup')
            elif 'ci' in item.file_path.lower() or 'workflow' in item.file_path.lower():
                improvements.append('CI/CD pipeline')
            elif 'docker' in item.file_path.lower():
                improvements.append('containerization')
            else:
                improvements.append('development workflow')

        if len(plan.items) > 3:
            improvements.append(f'and {len(plan.items) - 3} more improvements')

        return ', '.join(improvements)

    def _get_recent_activity_summary(self, analysis: AnalysisResult) -> str:
        """Get a summary of recent repository activity"""
        if analysis.last_updated:
            days_since_update = (datetime.now() - analysis.last_updated).days
            if days_since_update < 7:
                return "actively maintained"
            elif days_since_update < 30:
                return "recently updated"
            else:
                return "could benefit from fresh contributions"
        return "ready for improvements"

    def _truncate_message(self, message: str, max_length: int) -> str:
        """Truncate message to fit length limit while preserving structure"""
        if len(message) <= max_length:
            return message

        # Try to truncate at sentence boundary
        sentences = message.split('. ')
        truncated = ""

        for sentence in sentences:
            if len(truncated + sentence + '. ') <= max_length - 20:  # Leave room for closing
                truncated += sentence + '. '
            else:
                break

        # Add closing if truncated
        if truncated:
            truncated += "\n\nI'd love to discuss this further!"
        else:
            # Fallback: hard truncate
            truncated = message[:max_length-20] + "...\n\nLet's connect!"

        return truncated

    def _get_initial_contact_template(self) -> str:
        """Initial contact email template"""
        return """Hi {{ to_name }},

I hope this message finds you well! I've been exploring {{ company }}'s open source projects and was impressed by {{ repo_name }} - particularly {{ repo_description or "the quality of the codebase" }}.

I noticed some opportunities to contribute to the project's development workflow, including {{ contribution_summary }}. I've prepared {{ contribution_count }} specific improvements that could enhance the project's maintainability and developer experience.

The changes would take approximately {{ estimated_time }} to implement and include:
- Enhanced documentation and setup instructions
- Standardized build and testing workflows  
- Automated code quality checks

I have experience with {{ repo_language }} and DevOps practices, and I'd be happy to submit these improvements as pull requests. You can see my work at {{ github_profile }}.

Would you be open to me contributing these enhancements? I'm also interested in learning more about potential DevOps opportunities at {{ company }}, particularly in a {{ preferred_work_mode or "part-time" }} capacity.

Best regards,
{{ your_name }}

GitHub: {{ github_profile }}
Email: {{ your_email }}"""

    def _get_follow_up_template(self) -> str:
        """Follow-up email template"""
        return """Hi {{ to_name }},

I wanted to follow up on my previous message about contributing to {{ repo_name }}. 

I've since refined the improvement proposals and they're ready to implement. The contributions would add significant value to the project's developer experience, particularly around {{ contribution_summary }}.

If there's a better time to discuss this or if you'd prefer a different approach to contributions, please let me know. I'm flexible and eager to help improve {{ repo_name }}.

I'm also still very interested in exploring DevOps opportunities with {{ company }} and would appreciate any guidance on your hiring process.

Thank you for your time!

Best regards,
{{ your_name }}

{{ github_profile }}"""

    def _get_job_inquiry_template(self) -> str:
        """Job inquiry email template"""
        return """Subject: DevOps Engineer Position - Portfolio Review

Dear {{ to_name }},

I'm reaching out to express my strong interest in DevOps and System Architect opportunities at {{ company }}. Your work with {{ company_tech_stack or "modern technologies" }} aligns perfectly with my experience and passion.

About my background:
- {{ your_experience_years }} years of DevOps and infrastructure experience
- {{ contribution_count }}+ open source contributions focusing on CI/CD, automation, and developer workflows
- Strong expertise in {{ company_tech_stack or "cloud technologies, containerization, and automation" }}

I've been actively contributing to {{ company }}'s open source projects, demonstrating my ability to understand and improve complex systems. My recent contributions include workflow automation, testing enhancements, and documentation improvements.

I'm particularly interested in {{ preferred_work_mode }} arrangements and would love to discuss how my skills could benefit {{ company }}'s infrastructure and development teams.

Portfolio highlights:
{% for highlight in portfolio_highlights %}
- {{ highlight }}
{% endfor %}

You can review my work at:
- GitHub: {{ github_profile }}
- LinkedIn: {{ linkedin_profile }}

I'd appreciate the opportunity to discuss how I can contribute to {{ company }}'s continued success.

Best regards,
{{ your_name }}
{{ your_email }}"""

    def _get_maintainer_contact_template(self) -> str:
        """Template for contacting project maintainers"""
        return """Hi {{ to_name }},

I've been using {{ repo_name }} and really appreciate the work you've put into it! The {{ repo_language }} implementation is {{ recent_activity }}.

I've identified some areas where I could contribute to improve the developer experience:

{{ contribution_summary }}

These improvements would:
- Make the project more accessible to new contributors
- Standardize the development workflow
- Add automated quality checks
- Improve documentation and setup process

I have experience with {{ repo_language }} and modern DevOps practices. The changes would take about {{ estimated_time }} and I'm happy to implement them incrementally via pull requests.

{% if help_wanted_count > 0 %}
I also noticed you have {{ help_wanted_count }} "help wanted" issues - I'd be glad to tackle some of those as well!
{% endif %}

Would you be interested in these contributions? I'm committed to following your project's guidelines and working collaboratively with the team.

Thanks for maintaining such a valuable project!

Best,
{{ your_name }}
{{ github_profile }}"""

    def _get_linkedin_template(self) -> str:
        """LinkedIn message template"""
        return """Hi {{ to_name }},

I've been contributing to {{ company }}'s open source projects, particularly {{ repo_name }}, and I'm impressed by your team's technical approach.

I specialize in DevOps automation and have been working on improvements for {{ repo_name }} including {{ contribution_summary }}. 

I'm interested in learning more about {{ company }}'s infrastructure challenges and would love to connect. I'm particularly drawn to {{ preferred_work_mode }} DevOps roles where I can make a meaningful impact.

Would you be open to a brief conversation about opportunities at {{ company }}?

Best regards,
{{ your_name }}

Portfolio: {{ github_profile }}"""

    def get_template_names(self) -> List[str]:
        """Get list of available template names"""
        return list(self.templates.keys())

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a specific template"""
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")

        template = self.templates[template_name]
        return {
            'name': template.name,
            'tone': template.tone,
            'max_length': template.max_length,
            'use_html': template.use_html,
            'subject_template': template.subject_template,
            'description': self._get_template_description(template_name)
        }

    def _get_template_description(self, template_name: str) -> str:
        """Get description for a template"""
        descriptions = {
            'initial_contact': 'First outreach to introduce contributions and express interest',
            'follow_up': 'Follow-up message for non-responders',
            'job_inquiry': 'Direct inquiry about job opportunities',
            'maintainer_contact': 'Message focused on project contributions for maintainers',
            'linkedin_message': 'Professional networking message for LinkedIn'
        }
        return descriptions.get(template_name, 'Custom email template')

    def validate_context(self, template_name: str, context: Dict[str, Any]) -> List[str]:
        """Validate that context contains required variables for template"""
        required_vars = {
            'initial_contact': ['company', 'repo_name', 'contribution_summary', 'your_name'],
            'follow_up': ['to_name', 'repo_name', 'company', 'your_name'],
            'job_inquiry': ['company', 'your_name', 'github_profile'],
            'maintainer_contact': ['repo_name', 'contribution_summary', 'your_name'],
            'linkedin_message': ['company', 'repo_name', 'your_name']
        }

        missing_vars = []
        if template_name in required_vars:
            for var in required_vars[template_name]:
                if var not in context or not context[var]:
                    missing_vars.append(var)

        return missing_vars