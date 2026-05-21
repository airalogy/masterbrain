"""Unit tests for workspace manager helpers."""

from masterbrain.workspace_manager import WorkspaceManager


def test_select_root_prefers_native_picker(monkeypatch, tmp_path):
    manager = WorkspaceManager()

    monkeypatch.setattr(
        "masterbrain.workspace_manager._select_directory_native",
        lambda: str(tmp_path),
    )

    selected = manager.select_root()

    assert selected == tmp_path.resolve()
    assert manager.current_root() == tmp_path.resolve()
