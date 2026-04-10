"""Tests for desktop bundle packaging helpers."""

from __future__ import annotations

import stat

from masterbrain.build_desktop_bundle import (
    _build_macos_app_bundle,
    _build_windows_distribution,
    _platform_slug,
    _render_macos_info_plist,
    _render_windows_installer_script,
)
from masterbrain.desktop import _desktop_argv


def test_platform_slug_normalizes_operating_system_and_architecture() -> None:
    assert _platform_slug("Darwin", "arm64") == "macos-arm64"
    assert _platform_slug("Windows", "AMD64") == "windows-x64"
    assert _platform_slug("Linux", "x86_64") == "linux-x64"


def test_render_macos_info_plist_declares_aira_document_type() -> None:
    content = _render_macos_info_plist("0.7.0")

    assert "<string>Masterbrain</string>" in content
    assert "<string>aira</string>" in content
    assert "<string>Airalogy Archive</string>" in content


def test_build_macos_app_bundle_creates_launcher_and_archive(tmp_path) -> None:
    bundle_output = tmp_path / "dist" / "Masterbrain"
    binary = bundle_output / "Masterbrain"
    (bundle_output / "vendor" / "opencode").mkdir(parents=True)
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    release_root = tmp_path / "release" / "macos-arm64"
    artifacts = _build_macos_app_bundle(
        bundle_output=bundle_output,
        release_root=release_root,
        version="0.7.0",
        platform_slug="macos-arm64",
    )

    app_bundle = release_root / "Masterbrain.app"
    launcher = app_bundle / "Contents" / "MacOS" / "Masterbrain"
    embedded_binary = app_bundle / "Contents" / "Resources" / "Masterbrain" / "Masterbrain"
    archive_path = release_root / "Masterbrain-0.7.0-macos-arm64.zip"

    assert app_bundle in artifacts
    assert archive_path in artifacts
    assert embedded_binary.exists()
    assert launcher.exists()
    assert launcher.stat().st_mode & stat.S_IXUSR
    assert archive_path.exists()


def test_render_windows_installer_script_registers_aira_association(tmp_path) -> None:
    portable_dir = tmp_path / "release" / "windows-x64" / "Masterbrain"
    portable_dir.mkdir(parents=True)

    content = _render_windows_installer_script("0.7.0", portable_dir, portable_dir.parent)

    assert "ChangesAssociations=yes" in content
    assert "Software\\Classes\\.aira\\OpenWithProgids" in content
    assert 'Filename: "{app}\\{#MyAppExeName}"' in content


def test_build_windows_distribution_writes_portable_zip_and_installer_script(tmp_path) -> None:
    bundle_output = tmp_path / "dist" / "Masterbrain"
    binary = bundle_output / "Masterbrain.exe"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text("echo off\r\n", encoding="utf-8")

    release_root = tmp_path / "release" / "windows-x64"
    artifacts = _build_windows_distribution(
        bundle_output=bundle_output,
        release_root=release_root,
        version="0.7.0",
        compiler=None,
    )

    portable_dir = release_root / "Masterbrain"
    archive_path = release_root / "Masterbrain-0.7.0-windows-x64-portable.zip"
    iss_path = release_root / "Masterbrain-0.7.0-windows-x64-setup.iss"

    assert portable_dir in artifacts
    assert archive_path in artifacts
    assert iss_path in artifacts
    assert (portable_dir / "Masterbrain.exe").exists()
    assert archive_path.exists()
    assert iss_path.exists()


def test_desktop_argv_strips_macos_finder_psn_argument() -> None:
    assert _desktop_argv(["-psn_0_12345", "/tmp/demo.aira"]) == ["/tmp/demo.aira"]
    assert _desktop_argv(["--no-browser"]) == ["--no-browser"]
