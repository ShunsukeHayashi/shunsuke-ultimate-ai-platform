"""
Ultimate ShunsukeModel Ecosystem Setup
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-'):
            requirements.append(line)

setup(
    name="ultimate-shunsuke-ecosystem",
    version="1.0.0",
    author="ShunsukeModel Team",
    author_email="team@shunsuke-ecosystem.dev",
    description="Next-generation AI development platform with multi-agent orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shunsuke-dev/ultimate-shunsuke-ecosystem",
    project_urls={
        "Bug Tracker": "https://github.com/shunsuke-dev/ultimate-shunsuke-ecosystem/issues",
        "Documentation": "https://docs.shunsuke-ecosystem.dev",
        "Source Code": "https://github.com/shunsuke-dev/ultimate-shunsuke-ecosystem",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.4.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
        ],
        "cloud": [
            "azure-openai>=1.0.0",
            "google-cloud-aiplatform>=1.35.0",
            "boto3>=1.28.0",
        ],
        "monitoring": [
            "prometheus-client>=0.17.0",
            "grafana-api>=1.0.3",
            "datadog>=0.47.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "shunsuke-ecosystem=core.command_tower.cli:main",
            "shunsuke-agent=orchestration.coordinator.cli:main",
            "shunsuke-quality=tools.quality_analyzer.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md", "*.txt"],
    },
    zip_safe=False,
    keywords=[
        "ai",
        "development",
        "automation",
        "multi-agent",
        "quality-assurance",
        "claude",
        "mcp",
        "github-actions",
        "orchestration",
        "monitoring"
    ],
)