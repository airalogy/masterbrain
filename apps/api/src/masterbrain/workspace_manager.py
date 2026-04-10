"""Stateful local-workspace manager for desktop-style Masterbrain sessions."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from threading import Lock


IGNORED_DIR_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}
MAX_FILE_SIZE_BYTES = 1_000_000


def detect_type(filename: str) -> str:
    if filename.endswith(".aimd"):
        return "aimd"
    if filename.endswith(".py"):
        return "py"
    return "other"


def _is_ignored_rel_path(rel_path: PurePosixPath) -> bool:
    return any(part.startswith(".") or part in IGNORED_DIR_NAMES for part in rel_path.parts)


def _safe_root(path_like: str | Path) -> Path:
    path = Path(path_like).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"Workspace directory does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Workspace path is not a directory: {path}")
    return path


def _safe_workspace_path(root: Path, rel_path: str) -> Path:
    pure = PurePosixPath(rel_path)
    if pure.is_absolute():
        raise ValueError(f"Absolute paths are not allowed: {rel_path}")
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"Unsafe relative path: {rel_path}")

    candidate = (root / pure.as_posix()).resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError(f"Path escapes workspace root: {rel_path}")
    return candidate


def _looks_like_text_file(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return False
        with path.open("rb") as handle:
            sample = handle.read(2048)
    except OSError:
        return False

    return b"\x00" not in sample


def _can_open_directory_picker() -> bool:
    if sys.platform == "darwin" and shutil.which("osascript"):
        return True
    if os.name == "nt" and (shutil.which("powershell") or shutil.which("pwsh")):
        return True
    if shutil.which("zenity") or shutil.which("kdialog"):
        return True

    try:
        import tkinter  # noqa: F401
        from tkinter import filedialog  # noqa: F401
    except Exception:
        return False
    return True


def _select_directory_native() -> str | None:
    if sys.platform == "darwin" and shutil.which("osascript"):
        command = [
            "osascript",
            "-e",
            'try',
            "-e",
            'POSIX path of (choose folder with prompt "Choose a Masterbrain workspace directory")',
            "-e",
            "on error number -128",
            "-e",
            'return ""',
            "-e",
            "end try",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "macOS directory picker failed.")
        return result.stdout.strip() or None

    if os.name == "nt":
        shell = shutil.which("powershell") or shutil.which("pwsh")
        if shell:
            script = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
                "$dialog.Description = 'Choose a Masterbrain workspace directory'; "
                "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) "
                "{ Write-Output $dialog.SelectedPath }"
            )
            result = subprocess.run(
                [shell, "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "Windows directory picker failed.")
            return result.stdout.strip() or None

    if shutil.which("zenity"):
        result = subprocess.run(
            [
                "zenity",
                "--file-selection",
                "--directory",
                "--title=Choose a Masterbrain workspace directory",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
        if result.returncode in {1, 5}:
            return None
        raise RuntimeError(result.stderr.strip() or "Zenity directory picker failed.")

    if shutil.which("kdialog"):
        result = subprocess.run(
            ["kdialog", "--getexistingdirectory", str(Path.home())],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
        if result.returncode == 1:
            return None
        raise RuntimeError(result.stderr.strip() or "KDialog directory picker failed.")

    return None


class WorkspaceManager:
    """Single-user workspace selection and file IO for local desktop usage."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._root = self._initial_root()

    def _initial_root(self) -> Path | None:
        configured = os.getenv("MASTERBRAIN_WORKSPACE_DIR")
        if not configured:
            return None
        return _safe_root(configured)

    def has_workspace(self) -> bool:
        return self._root is not None

    def current_root(self) -> Path | None:
        return self._root

    def ensure_root(self) -> Path:
        if self._root is None:
            raise ValueError("No workspace directory is selected.")
        return self._root

    def set_root(self, path_like: str | Path) -> Path:
        root = _safe_root(path_like)
        with self._lock:
            self._root = root
        return root

    def select_root(self) -> Path:
        selected = _select_directory_native()
        if selected is None and not _can_open_directory_picker():
            raise RuntimeError("Directory picker is not available in this environment.")

        if selected is None:
            import tkinter as tk
            from tkinter import filedialog

            root_window = tk.Tk()
            root_window.withdraw()
            root_window.attributes("-topmost", True)
            try:
                selected = filedialog.askdirectory(
                    title="Choose a Masterbrain workspace directory",
                    mustexist=True,
                )
            finally:
                root_window.destroy()

        if not selected:
            raise ValueError("No workspace directory was selected.")
        return self.set_root(selected)

    def snapshot(self) -> dict:
        root = self.current_root()
        if root is None:
            return {
                "mode": "directory",
                "has_workspace": False,
                "root_path": None,
                "files": [],
                "folders": [],
                "entry_count": 0,
                "can_select_directory": _can_open_directory_picker(),
            }

        files, folders, entry_count = self._collect_entries(root)
        return {
            "mode": "directory",
            "has_workspace": True,
            "root_path": str(root),
            "files": files,
            "folders": folders,
            "entry_count": entry_count,
            "can_select_directory": _can_open_directory_picker(),
        }

    def _collect_entries(self, root: Path) -> tuple[list[dict], list[str], int]:
        files: list[dict] = []
        folders: set[str] = set()
        entry_count = 0

        for current_dir, dirnames, filenames in os.walk(root):
            dir_path = Path(current_dir)
            rel_dir = dir_path.relative_to(root)

            dirnames[:] = [
                dirname
                for dirname in dirnames
                if not _is_ignored_rel_path(rel_dir / dirname)
            ]

            if dir_path != root:
                folders.add(rel_dir.as_posix())
                entry_count += 1

            for filename in filenames:
                path = dir_path / filename
                rel_path = path.relative_to(root).as_posix()
                rel_pure = PurePosixPath(rel_path)
                if _is_ignored_rel_path(rel_pure):
                    continue
                entry_count += 1
                if not _looks_like_text_file(path):
                    continue

                files.append(
                    {
                        "name": path.name,
                        "path": rel_path,
                        "content": path.read_text(encoding="utf-8", errors="ignore"),
                        "type": detect_type(path.name),
                    }
                )

        files.sort(key=lambda item: item["path"])
        return files, sorted(folders), entry_count

    def _clear_workspace_contents(self, root: Path) -> None:
        for child in root.iterdir():
            rel_path = PurePosixPath(child.name)
            if _is_ignored_rel_path(rel_path):
                continue
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()

    def _iter_archive_members(self, archive: zipfile.ZipFile) -> list[tuple[PurePosixPath, zipfile.ZipInfo]]:
        members: list[tuple[PurePosixPath, zipfile.ZipInfo]] = []
        for info in archive.infolist():
            raw_name = info.filename.replace("\\", "/").strip()
            if not raw_name:
                continue
            rel_path = PurePosixPath(raw_name)
            if rel_path.is_absolute():
                raise ValueError(f"ZIP contains an absolute path: {info.filename}")
            if any(part in {"", ".", ".."} for part in rel_path.parts):
                raise ValueError(f"ZIP contains an unsafe path: {info.filename}")
            if _is_ignored_rel_path(rel_path):
                continue
            members.append((rel_path, info))
        return members

    def write_file(self, rel_path: str, content: str) -> None:
        root = self.ensure_root()
        path = _safe_workspace_path(root, rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def create_file(self, rel_path: str, content: str = "") -> None:
        self.write_file(rel_path, content)

    def delete_file(self, rel_path: str) -> None:
        root = self.ensure_root()
        path = _safe_workspace_path(root, rel_path)
        if not path.exists():
            return
        if path.is_dir():
            raise ValueError(f"Expected a file path but got a directory: {rel_path}")
        path.unlink()

    def rename_file(self, old_rel_path: str, new_name: str) -> str:
        if "/" in new_name or "\\" in new_name:
            raise ValueError("Rename expects a file name, not a nested path.")

        root = self.ensure_root()
        old_path = _safe_workspace_path(root, old_rel_path)
        if not old_path.exists():
            raise ValueError(f"File does not exist: {old_rel_path}")

        parent = PurePosixPath(old_rel_path).parent
        new_rel_path = (parent / new_name).as_posix() if str(parent) != "." else new_name
        new_path = _safe_workspace_path(root, new_rel_path)

        if new_path.exists() and new_path != old_path:
            raise ValueError(f"Target file already exists: {new_rel_path}")

        old_path.rename(new_path)
        return new_rel_path

    def create_folder(self, rel_path: str) -> None:
        root = self.ensure_root()
        path = _safe_workspace_path(root, rel_path)
        path.mkdir(parents=True, exist_ok=True)

    def replace_with_directory(self, source_root: str | Path) -> None:
        source = _safe_root(source_root)
        root = self.ensure_root()
        self._clear_workspace_contents(root)

        for current_dir, dirnames, filenames in os.walk(source):
            dir_path = Path(current_dir)
            rel_dir = dir_path.relative_to(source)

            dirnames[:] = [
                dirname
                for dirname in dirnames
                if not _is_ignored_rel_path(rel_dir / dirname)
            ]

            for dirname in dirnames:
                target_dir = _safe_workspace_path(
                    root,
                    (rel_dir / dirname).as_posix(),
                )
                target_dir.mkdir(parents=True, exist_ok=True)

            for filename in filenames:
                rel_path = rel_dir / filename
                if _is_ignored_rel_path(rel_path):
                    continue
                source_file = dir_path / filename
                target_file = _safe_workspace_path(root, rel_path.as_posix())
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)

    def import_zip_bytes(self, payload: bytes) -> None:
        root = self.ensure_root()
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                members = self._iter_archive_members(archive)
                self._clear_workspace_contents(root)
                for rel_path, info in members:
                    target = _safe_workspace_path(root, rel_path.as_posix())
                    if info.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info, "r") as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
        except zipfile.BadZipFile as exc:
            raise ValueError("Uploaded file is not a valid ZIP archive.") from exc

    def export_zip_bytes(self) -> tuple[str, bytes]:
        root = self.ensure_root()
        archive_name = f"{root.name or 'workspace'}.zip"
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for current_dir, dirnames, filenames in os.walk(root):
                dir_path = Path(current_dir)
                rel_dir = dir_path.relative_to(root)

                dirnames[:] = [
                    dirname
                    for dirname in dirnames
                    if not _is_ignored_rel_path(rel_dir / dirname)
                ]

                if dir_path != root and not dirnames and not filenames:
                    archive.writestr(f"{rel_dir.as_posix()}/", b"")

                for filename in filenames:
                    path = dir_path / filename
                    rel_path = path.relative_to(root).as_posix()
                    if _is_ignored_rel_path(PurePosixPath(rel_path)):
                        continue
                    archive.write(path, rel_path)

        return archive_name, buffer.getvalue()


workspace_manager = WorkspaceManager()
