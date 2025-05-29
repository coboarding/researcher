devops-researcher/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── companies.json
├── src/
│   ├── __init__.py
│   ├── github_client.py
│   ├── repo_analyzer.py
│   ├── contribution_generator.py
│   ├── report_generator.py
│   └── email_templates.py
├── scripts/
│   ├── main.py
│   ├── analyze_companies.py
│   ├── generate_contributions.py
│   └── send_outreach.py
├── tests/
│   ├── __init__.py
│   ├── test_github_client.py
│   ├── test_repo_analyzer.py
│   └── test_contribution_generator.py
├── templates/
│   ├── email_template.txt
│   ├── linkedin_template.txt
│   └── readme_improvement.md
├── output/
│   ├── reports/
│   ├── contributions/
│   └── logs/
├── docs/
│   ├── setup.md
│   ├── usage.md
│   └── api.md
└── Makefile