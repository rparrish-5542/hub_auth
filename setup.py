"""Setup configuration for hub-auth-client package."""
from setuptools import setup, find_packages

with open("README_PACKAGE.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hub-auth-client",
    version="1.0.34",
    author="rparrish-5542",
    author_email="rparrish@example.com",
    description="MSAL JWT validation library with Entra ID RBAC support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rparrish-5542/hub_auth",
    packages=find_packages(exclude=["tests", "tests.*", "hub_auth", "authentication", "services"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 5.0",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyJWT>=2.8.0",
        "cryptography>=41.0.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "django": [
            "Django>=4.2",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-django>=4.5.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="msal jwt azure entra authentication rbac validation",
    project_urls={
        "Bug Reports": "https://github.com/rparrish-5542/hub_auth/issues",
        "Source": "https://github.com/rparrish-5542/hub_auth",
    },
)
