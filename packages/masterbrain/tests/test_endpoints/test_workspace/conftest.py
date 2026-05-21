"""Test configuration for workspace endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from masterbrain.fastapi.main import app
from masterbrain.workspace_manager import workspace_manager


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def workspace_root(tmp_path, monkeypatch):
    """Point the singleton workspace manager at a temporary directory."""
    original_root = workspace_manager.current_root()
    monkeypatch.setattr(workspace_manager, "_root", tmp_path)
    yield tmp_path
    monkeypatch.setattr(workspace_manager, "_root", original_root)
