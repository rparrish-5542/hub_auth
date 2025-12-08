"""Test configuration for pytest."""

import os
import sys
from pathlib import Path

# Add the hub_auth_client package to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set Django settings module for Django tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')
