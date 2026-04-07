import sys
import os

import pytest

# Ensure project root is on sys.path so `silly_engine` imports resolve
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def pytest_configure(config):
    config.addinivalue_line("markers", "postgres: tests requiring a running PostgreSQL server")
