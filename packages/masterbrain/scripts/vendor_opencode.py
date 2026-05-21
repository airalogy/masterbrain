#!/usr/bin/env python3
"""Download and vendor the official OpenCode CLI for packaging.

This follows the official OpenCode install asset naming convention:
https://raw.githubusercontent.com/anomalyco/opencode/dev/install
"""

from __future__ import annotations

import argparse
import io
import json
import os
import platform
import shutil
import stat
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path


SUPPORTED_TARGETS = {
    "darwin-arm64",
    "darwin-x64",
    "darwin-x64-baseline",
    "linux-x64",
    "linux-x64-baseline",
    "linux-x64-musl",
    "linux-x64-baseline-musl",
    "linux-arm64",
    "linux-arm64-musl",
    "windows-x64",
}


def current_target() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    os_name = {
        "darwin": "darwin",
        "linux": "linux",
        "windows": "windows",
    }.get(system)
    if not os_name:
        raise SystemExit(f"Unsupported operating system: {system}")

    arch = {
        "arm64": "arm64",
        "aarch64": "arm64",
        "x86_64": "x64",
        "amd64": "x64",
    }.get(machine)
    if not arch:
        raise SystemExit(f"Unsupported CPU architecture: {machine}")

    if os_name == "windows" and arch != "x64":
        raise SystemExit("Official OpenCode release assets currently support only windows-x64.")

    return f"{os_name}-{arch}"


def asset_filename(target: str) -> str:
    ext = ".tar.gz" if target.startswith("linux") else ".zip"
    return f"opencode-{target}{ext}"


def release_url(target: str, version: str | None) -> str:
    filename = asset_filename(target)
    if version:
        version = version.removeprefix("v")
        return f"https://github.com/anomalyco/opencode/releases/download/v{version}/{filename}"
    return f"https://github.com/anomalyco/opencode/releases/latest/download/{filename}"


def latest_version() -> str:
    with urllib.request.urlopen(
        "https://api.github.com/repos/anomalyco/opencode/releases/latest"
    ) as response:
        payload = json.load(response)
    tag_name = str(payload["tag_name"])
    return tag_name.removeprefix("v")


def download(url: str) -> bytes:
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as response:
        return response.read()


def extract_archive(archive_bytes: bytes, target_dir: Path, target: str) -> Path:
    if target.startswith("linux"):
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            archive.extractall(target_dir)
    else:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            archive.extractall(target_dir)

    binary_name = "opencode.exe" if target.startswith("windows") else "opencode"
    matches = sorted(target_dir.rglob(binary_name))
    if not matches:
        raise SystemExit(f"Failed to locate {binary_name} after extracting OpenCode.")
    return matches[0]


def main() -> None:
    api_root = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser(description="Vendor the OpenCode CLI for packaging.")
    parser.add_argument(
        "--target",
        default=os.getenv("MASTERBRAIN_OPENCODE_TARGET") or current_target(),
        help="Target slug, for example darwin-arm64 or linux-x64.",
    )
    parser.add_argument(
        "--version",
        default=os.getenv("MASTERBRAIN_OPENCODE_VERSION"),
        help="Specific OpenCode version without the leading v. Defaults to latest.",
    )
    parser.add_argument(
        "--output-root",
        default=str(api_root / "vendor" / "opencode"),
        help="Directory where the vendored OpenCode binary should be stored.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing vendored target directory.",
    )
    args = parser.parse_args()

    target = args.target
    if target not in SUPPORTED_TARGETS:
        raise SystemExit(
            f"Unsupported target `{target}`. Supported targets: {', '.join(sorted(SUPPORTED_TARGETS))}"
        )

    version = args.version or latest_version()
    destination_root = Path(args.output_root).resolve()
    destination_dir = destination_root / target

    if destination_dir.exists():
        if not args.force:
            print(f"Vendored OpenCode already exists at {destination_dir}")
            return
        shutil.rmtree(destination_dir)

    destination_dir.mkdir(parents=True, exist_ok=True)

    url = release_url(target, version)
    archive_bytes = download(url)

    temp_extract_dir = destination_dir / "_extract"
    temp_extract_dir.mkdir(parents=True, exist_ok=True)
    binary_path = extract_archive(archive_bytes, temp_extract_dir, target)

    final_binary_name = "opencode.exe" if target.startswith("windows") else "opencode"
    final_binary_path = destination_dir / final_binary_name
    shutil.move(str(binary_path), str(final_binary_path))

    if not target.startswith("windows"):
        final_binary_path.chmod(final_binary_path.stat().st_mode | stat.S_IXUSR)

    shutil.rmtree(temp_extract_dir, ignore_errors=True)
    (destination_dir / "VERSION").write_text(version + "\n", encoding="utf-8")
    (destination_dir / "SOURCE_URL").write_text(url + "\n", encoding="utf-8")

    print(f"Vendored OpenCode {version} to {final_binary_path}")


if __name__ == "__main__":
    main()
