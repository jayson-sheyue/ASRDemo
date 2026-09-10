"""Keep tests offline. Must run before app.py calls load_dotenv."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['GOOGLE_CLOUD_PROJECT'] = ''
os.environ['GOOGLE_CLOUD_LOCATION'] = 'us'


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app import app
    with TestClient(app) as test_client:
        yield test_client
