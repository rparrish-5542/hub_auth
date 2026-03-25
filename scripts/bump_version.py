#!/usr/bin/env python3
"""Version bumping script for hub-auth-client."""
import re
import sys
from pathlib import Path


def bump_version(version_type: str) -> tuple[str, str]:
    """Bump version in pyproject.toml and setup.py.
    
    Args:
        version_type: One of 'major', 'minor', or 'patch'
        
    Returns:
        Tuple of (current_version, new_version)
    """
    # Read current version from pyproject.toml
    pyproject_path = Path('pyproject.toml')
    pyproject_content = pyproject_path.read_text()
    
    version_match = re.search(r'version = "(\d+\.\d+\.\d+)"', pyproject_content)
    if not version_match:
        print("ERROR: Could not find version in pyproject.toml")
        sys.exit(1)
    
    current_version = version_match.group(1)
    major, minor, patch = map(int, current_version.split('.'))
    
    # Calculate new version
    if version_type == 'major':
        new_version = f"{major + 1}.0.0"
    elif version_type == 'minor':
        new_version = f"{major}.{minor + 1}.0"
    elif version_type == 'patch':
        new_version = f"{major}.{minor}.{patch + 1}"
    else:
        print(f"ERROR: Invalid version_type: {version_type}")
        sys.exit(1)
    
    print(f"Bumping version: {current_version} -> {new_version}")
    
    # Update pyproject.toml
    new_pyproject_content = pyproject_content.replace(
        f'version = "{current_version}"',
        f'version = "{new_version}"'
    )
    pyproject_path.write_text(new_pyproject_content)
    print("✓ Updated pyproject.toml")
    
    # Update setup.py
    setup_path = Path('setup.py')
    if setup_path.exists():
        setup_content = setup_path.read_text()
        new_setup_content = setup_content.replace(
            f'version="{current_version}"',
            f'version="{new_version}"'
        )
        setup_path.write_text(new_setup_content)
        print("✓ Updated setup.py")
    else:
        print("⚠ setup.py not found, skipping")
    
    return current_version, new_version


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: bump_version.py <major|minor|patch>")
        sys.exit(1)
    
    version_type = sys.argv[1]
    current, new = bump_version(version_type)
    
    # Output for GitHub Actions
    print(f"::set-output name=current_version::{current}")
    print(f"::set-output name=new_version::{new}")
