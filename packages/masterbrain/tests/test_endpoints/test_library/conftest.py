"""Test configuration for library endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from masterbrain.fastapi.main import app
from masterbrain.library_store import library_store
from masterbrain.workspace_manager import workspace_manager


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def library_db_path(tmp_path, monkeypatch):
    original_path = getattr(library_store, "_db_path")
    test_db = tmp_path / "library.db"
    library_store.set_db_path(test_db)
    yield test_db
    monkeypatch.setattr(library_store, "_db_path", original_path)


@pytest.fixture
def workspace_root(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    root.mkdir()
    original_root = workspace_manager.current_root()
    monkeypatch.setattr(workspace_manager, "_root", root)
    yield root
    monkeypatch.setattr(workspace_manager, "_root", original_root)
