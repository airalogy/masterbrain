"""Helpers for resolving a bundled or system OpenCode binary."""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path


def current_opencode_target() -> str:
    """Return the current OS/arch target slug used by OpenCode release assets."""

    system = platform.system().lower()
    machine = platform.machine().lower()

    os_name = {
        "darwin": "darwin",
        "linux": "linux",
        "windows": "windows",
    }.get(system)
    if not os_name:
        raise RuntimeError(f"Unsupported operating system for OpenCode: {system}")

    arch = {
        "arm64": "arm64",
        "aarch64": "arm64",
        "x86_64": "x64",
        "amd64": "x64",
    }.get(machine)
    if not arch:
        raise RuntimeError(f"Unsupported CPU architecture for OpenCode: {machine}")

    if os_name == "windows" and arch != "x64":
        raise RuntimeError(
            f"Unsupported OpenCode Windows target: {os_name}/{machine}. "
            "The official installer currently supports windows-x64."
        )

    return f"{os_name}-{arch}"


def _opencode_binary_name() -> str:
    return "opencode.exe" if platform.system().lower() == "windows" else "opencode"


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []

    env_dir = os.getenv("MASTERBRAIN_OPENCODE_DIR")
    if env_dir:
        roots.append(Path(env_dir).expanduser().resolve())

    app_root = Path(__file__).resolve().parents[3]
    roots.append(app_root / "vendor" / "opencode")

    if app_root.name == "api" and app_root.parent.name == "apps":
        repo_root = app_root.parents[1]
        roots.append(repo_root / "vendor" / "opencode")

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            roots.append(Path(meipass) / "vendor" / "opencode")

    return roots


def bundled_opencode_candidates() -> list[Path]:
    """Return possible bundled OpenCode binary paths for the current platform."""

    target = current_opencode_target()
    binary_name = _opencode_binary_name()
    candidates: list[Path] = []

    for root in _candidate_roots():
        candidates.append(root / target / binary_name)
        candidates.append(root / target / "bin" / binary_name)

    return candidates


def resolve_opencode_binary() -> Path | None:
    """Resolve the OpenCode binary from env override, bundled assets, or PATH."""

    env_bin = os.getenv("MASTERBRAIN_OPENCODE_BIN")
    if env_bin:
        candidate = Path(env_bin).expanduser().resolve()
        if candidate.exists():
            return candidate

    for candidate in bundled_opencode_candidates():
        if candidate.exists():
            return candidate

    from_path = shutil.which("opencode")
    if from_path:
        return Path(from_path).resolve()

    return None


def missing_opencode_message() -> str:
    """Return a user-facing error for when OpenCode cannot be resolved."""

    if getattr(sys, "frozen", False):
        return (
            "Masterbrain could not find its bundled OpenCode runtime. Reinstall the packaged "
            "application, or run Masterbrain from a source checkout with OpenCode installed "
            "locally."
        )

    return (
        "Masterbrain could not find an OpenCode runtime. Packaged desktop builds bundle "
        "OpenCode automatically. For source or development runs, either place `opencode` on "
        "PATH or vendor it with the `packages/masterbrain/scripts/vendor_opencode.py` helper."
    )
