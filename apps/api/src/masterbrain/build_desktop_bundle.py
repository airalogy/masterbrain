"""Cross-platform builder for the desktop-style Masterbrain bundle."""

from __future__ import annotations

import argparse
import os
import platform
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import textwrap
import tomllib
import zipfile
from pathlib import Path


def _api_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    return _api_root().parents[1]


def _workspace_root() -> Path:
    return _repo_root().parent


def _binary(name: str) -> str:
    if os.name != "nt":
        return name
    return {
        "npm": "npm.cmd",
    }.get(name, name)


def _run(command: list[str], cwd: Path) -> None:
    printable = " ".join(shlex.quote(part) for part in command)
    print(f"$ {printable}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def _remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def _preflight_requirements() -> None:
    workspace_root = _workspace_root()
    sibling_airalogy = workspace_root / "airalogy"
    sibling_aimd = workspace_root / "aimd"

    missing: list[str] = []
    if not sibling_airalogy.exists():
        missing.append(str(sibling_airalogy))
    if not sibling_aimd.exists():
        missing.append(str(sibling_aimd))

    if missing:
        joined = "\n".join(f"- {item}" for item in missing)
        raise SystemExit(
            "Masterbrain source builds expect sibling `airalogy/` and `aimd/` checkouts.\n"
            f"Missing paths:\n{joined}"
        )


def _project_version(api_root: Path) -> str:
    pyproject = api_root / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _normalized_machine(machine: str) -> str:
    return {
        "x86_64": "x64",
        "amd64": "x64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine.lower(), machine.lower())


def _platform_slug(system_name: str | None = None, machine: str | None = None) -> str:
    system_slug = {
        "darwin": "macos",
        "windows": "windows",
        "linux": "linux",
    }.get((system_name or platform.system()).lower())
    if system_slug is None:
        raise RuntimeError(f"Unsupported operating system: {system_name or platform.system()}")

    arch_slug = _normalized_machine(machine or platform.machine())
    return f"{system_slug}-{arch_slug}"


def _release_root(api_root: Path, platform_slug: str) -> Path:
    return api_root / "dist" / "release" / platform_slug


def _copy_bundle(bundle_output: Path, destination: Path) -> None:
    _remove_path(destination)
    shutil.copytree(bundle_output, destination)


def _zip_directory(source_dir: Path, archive_path: Path, root_name: str | None = None) -> None:
    _remove_path(archive_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    archive_root = root_name or source_dir.name
    with zipfile.ZipFile(
        archive_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir():
                continue
            arcname = Path(archive_root) / path.relative_to(source_dir)
            archive.write(path, arcname)


def _tar_directory(source_dir: Path, archive_path: Path, root_name: str | None = None) -> None:
    _remove_path(archive_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, mode="w:gz") as archive:
        archive.add(source_dir, arcname=root_name or source_dir.name)


def _write_executable_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _render_macos_info_plist(version: str) -> str:
    return textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>CFBundleDevelopmentRegion</key>
            <string>en</string>
            <key>CFBundleDisplayName</key>
            <string>Masterbrain</string>
            <key>CFBundleDocumentTypes</key>
            <array>
                <dict>
                    <key>CFBundleTypeExtensions</key>
                    <array>
                        <string>aira</string>
                    </array>
                    <key>CFBundleTypeName</key>
                    <string>Airalogy Archive</string>
                    <key>CFBundleTypeRole</key>
                    <string>Viewer</string>
                </dict>
            </array>
            <key>CFBundleExecutable</key>
            <string>Masterbrain</string>
            <key>CFBundleIdentifier</key>
            <string>org.airalogy.masterbrain</string>
            <key>CFBundleInfoDictionaryVersion</key>
            <string>6.0</string>
            <key>CFBundleName</key>
            <string>Masterbrain</string>
            <key>CFBundlePackageType</key>
            <string>APPL</string>
            <key>CFBundleShortVersionString</key>
            <string>{version}</string>
            <key>CFBundleVersion</key>
            <string>{version}</string>
            <key>LSMinimumSystemVersion</key>
            <string>11.0</string>
            <key>NSHighResolutionCapable</key>
            <true/>
        </dict>
        </plist>
        """
    )


def _build_macos_app_bundle(
    bundle_output: Path, release_root: Path, version: str, platform_slug: str
) -> list[Path]:
    app_bundle = release_root / "Masterbrain.app"
    contents_dir = app_bundle / "Contents"
    resources_dir = contents_dir / "Resources"
    macos_dir = contents_dir / "MacOS"
    embedded_bundle = resources_dir / "Masterbrain"

    _remove_path(app_bundle)
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)

    _copy_bundle(bundle_output, embedded_bundle)
    (contents_dir / "Info.plist").write_text(
        _render_macos_info_plist(version),
        encoding="utf-8",
    )
    (contents_dir / "PkgInfo").write_text("APPL????", encoding="ascii")

    launcher = macos_dir / "Masterbrain"
    _write_executable_text(
        launcher,
        textwrap.dedent(
            """\
            #!/bin/sh
            set -eu

            SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
            APP_ROOT="$SCRIPT_DIR/../Resources/Masterbrain"
            exec "$APP_ROOT/Masterbrain" "$@"
            """
        ),
    )

    archive_path = release_root / f"Masterbrain-{version}-{platform_slug}.zip"
    _zip_directory(app_bundle, archive_path, root_name="Masterbrain.app")

    return [app_bundle, archive_path]


def _render_windows_installer_script(
    version: str, portable_dir: Path, release_root: Path
) -> str:
    source_root = str(portable_dir.resolve()).replace("/", "\\")
    output_root = str(release_root.resolve()).replace("/", "\\")

    return textwrap.dedent(
        f"""\
        #define MyAppName "Masterbrain"
        #define MyAppVersion "{version}"
        #define MyAppPublisher "Airalogy MasterBrain Team"
        #define MyAppExeName "Masterbrain.exe"
        #define MySourceRoot "{source_root}"

        [Setup]
        AppId={{{{EAE4A3A1-E8E5-43E5-8F31-7E7A51D98C17}}}}
        AppName={{#MyAppName}}
        AppVersion={{#MyAppVersion}}
        AppPublisher={{#MyAppPublisher}}
        AppAssocRegView=64
        ChangesAssociations=yes
        Compression=lzma
        DefaultDirName={{localappdata}}\\Programs\\{{#MyAppName}}
        DefaultGroupName={{#MyAppName}}
        DisableDirPage=no
        DisableProgramGroupPage=yes
        OutputDir="{output_root}"
        OutputBaseFilename=Masterbrain-{version}-windows-x64-setup
        PrivilegesRequired=lowest
        SolidCompression=yes
        WizardStyle=modern
        ArchitecturesAllowed=x64compatible
        ArchitecturesInstallIn64BitMode=x64compatible
        UninstallDisplayIcon={{app}}\\{{#MyAppExeName}}

        [Tasks]
        Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

        [Files]
        Source: "{{#MySourceRoot}}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

        [Icons]
        Name: "{{autoprograms}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
        Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

        [Registry]
        Root: HKCU; Subkey: "Software\\Classes\\.aira\\OpenWithProgids"; ValueType: string; ValueName: "Masterbrain.AiraArchive"; ValueData: ""; Flags: uninsdeletevalue
        Root: HKCU; Subkey: "Software\\Classes\\Masterbrain.AiraArchive"; ValueType: string; ValueName: ""; ValueData: "Airalogy Archive"; Flags: uninsdeletekey
        Root: HKCU; Subkey: "Software\\Classes\\Masterbrain.AiraArchive\\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{{app}}\\{{#MyAppExeName}},0"
        Root: HKCU; Subkey: "Software\\Classes\\Masterbrain.AiraArchive\\shell\\open\\command"; ValueType: string; ValueName: ""; ValueData: """"{{app}}\\{{#MyAppExeName}}"""" """"%1""""

        [Run]
        Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "Launch {{#MyAppName}}"; Flags: nowait postinstall skipifsilent
        """
    )


def _find_inno_setup_compiler() -> Path | None:
    env_override = os.getenv("ISCC")
    if env_override:
        candidate = Path(env_override).expanduser().resolve()
        if candidate.exists():
            return candidate

    for command_name in ("iscc", "ISCC.exe"):
        resolved = shutil.which(command_name)
        if resolved:
            return Path(resolved).resolve()

    if os.name == "nt":
        for env_key in ("ProgramFiles", "ProgramFiles(x86)"):
            root = os.getenv(env_key)
            if not root:
                continue
            candidate = Path(root) / "Inno Setup 6" / "ISCC.exe"
            if candidate.exists():
                return candidate.resolve()

    return None


def _build_windows_distribution(
    bundle_output: Path,
    release_root: Path,
    version: str,
    compiler: Path | None,
) -> list[Path]:
    portable_dir = release_root / "Masterbrain"
    _copy_bundle(bundle_output, portable_dir)

    artifacts: list[Path] = [portable_dir]

    portable_archive = release_root / f"Masterbrain-{version}-windows-x64-portable.zip"
    _zip_directory(portable_dir, portable_archive)
    artifacts.append(portable_archive)

    iss_path = release_root / f"Masterbrain-{version}-windows-x64-setup.iss"
    iss_path.write_text(
        _render_windows_installer_script(version, portable_dir, release_root),
        encoding="utf-8",
    )
    artifacts.append(iss_path)

    iscc = compiler or _find_inno_setup_compiler()
    if iscc is None:
        print(
            "Inno Setup compiler not found; wrote the installer script but skipped .exe generation.",
            flush=True,
        )
        return artifacts

    _run([str(iscc), str(iss_path)], cwd=release_root)
    installer_path = release_root / f"Masterbrain-{version}-windows-x64-setup.exe"
    if installer_path.exists():
        artifacts.append(installer_path)

    return artifacts


def _build_linux_distribution(
    bundle_output: Path, release_root: Path, version: str, platform_slug: str
) -> list[Path]:
    portable_dir = release_root / "Masterbrain"
    _copy_bundle(bundle_output, portable_dir)

    archive_path = release_root / f"Masterbrain-{version}-{platform_slug}.tar.gz"
    _tar_directory(portable_dir, archive_path)

    return [portable_dir, archive_path]


def _build_release_artifacts(
    bundle_output: Path,
    api_root: Path,
    version: str,
    platform_slug: str,
    inno_setup_compiler: Path | None,
) -> list[Path]:
    release_root = _release_root(api_root, platform_slug)
    _remove_path(release_root)
    release_root.mkdir(parents=True, exist_ok=True)

    if platform_slug.startswith("macos-"):
        return _build_macos_app_bundle(bundle_output, release_root, version, platform_slug)
    if platform_slug.startswith("windows-"):
        return _build_windows_distribution(
            bundle_output,
            release_root,
            version,
            inno_setup_compiler,
        )
    if platform_slug.startswith("linux-"):
        return _build_linux_distribution(bundle_output, release_root, version, platform_slug)

    raise RuntimeError(f"Unsupported release packaging target: {platform_slug}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the local Masterbrain desktop-style bundle on the current platform."
    )
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Skip `npm install` and frontend build.",
    )
    parser.add_argument(
        "--skip-opencode",
        action="store_true",
        help="Skip vendoring the OpenCode CLI.",
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Skip `uv sync --group packaging` before PyInstaller.",
    )
    parser.add_argument(
        "--skip-release",
        action="store_true",
        help="Skip platform-specific release packaging after PyInstaller completes.",
    )
    parser.add_argument(
        "--opencode-target",
        help="Override the vendored OpenCode target slug, for example `windows-x64`.",
    )
    parser.add_argument(
        "--opencode-version",
        help="Vendor a specific OpenCode version without the leading `v`.",
    )
    parser.add_argument(
        "--inno-setup-compiler",
        help="Optional path to `ISCC.exe` for Windows installer compilation.",
    )
    parser.add_argument(
        "--no-force-opencode",
        action="store_true",
        help="Do not overwrite an existing vendored OpenCode target directory.",
    )
    parser.add_argument(
        "--pyinstaller-arg",
        action="append",
        default=[],
        help="Extra argument forwarded to PyInstaller. Repeat as needed.",
    )
    args = parser.parse_args()

    _preflight_requirements()

    api_root = _api_root()
    repo_root = _repo_root()
    web_root = repo_root / "apps" / "web"
    vendor_script = api_root / "scripts" / "vendor_opencode.py"
    bundle_output = api_root / "dist" / "Masterbrain"
    version = _project_version(api_root)
    platform_slug = _platform_slug()
    inno_setup_compiler = (
        Path(args.inno_setup_compiler).expanduser().resolve()
        if args.inno_setup_compiler
        else None
    )

    if not args.skip_frontend:
        print("[1/6] Building frontend", flush=True)
        _run([_binary("npm"), "install"], cwd=web_root)
        _run([_binary("npm"), "run", "build"], cwd=web_root)
    else:
        print("[1/6] Skipped frontend build", flush=True)

    if not args.skip_opencode:
        print("[2/6] Vendoring OpenCode CLI", flush=True)
        command = [sys.executable, str(vendor_script)]
        if not args.no_force_opencode:
            command.append("--force")
        if args.opencode_target:
            command.extend(["--target", args.opencode_target])
        if args.opencode_version:
            command.extend(["--version", args.opencode_version])
        _run(command, cwd=api_root)
    else:
        print("[2/6] Skipped OpenCode vendoring", flush=True)

    if not args.skip_sync:
        print("[3/6] Syncing Python packaging dependencies", flush=True)
        _run([_binary("uv"), "sync", "--group", "packaging"], cwd=api_root)
    else:
        print("[3/6] Skipped packaging dependency sync", flush=True)

    print("[4/6] Building desktop bundle with PyInstaller", flush=True)
    pyinstaller_command = [
        _binary("uv"),
        "run",
        "pyinstaller",
        "packaging/pyinstaller/masterbrain.spec",
        "--noconfirm",
        *args.pyinstaller_arg,
    ]
    _run(pyinstaller_command, cwd=api_root)

    release_artifacts: list[Path] = []
    if not args.skip_release:
        print(f"[5/6] Packaging release artifacts for {platform_slug}", flush=True)
        release_artifacts = _build_release_artifacts(
            bundle_output=bundle_output,
            api_root=api_root,
            version=version,
            platform_slug=platform_slug,
            inno_setup_compiler=inno_setup_compiler,
        )
    else:
        print("[5/6] Skipped release artifact packaging", flush=True)

    print("[6/6] Done", flush=True)
    print(f"Bundle output: {bundle_output}", flush=True)
    if release_artifacts:
        print("Release artifacts:", flush=True)
        for artifact in release_artifacts:
            print(f"- {artifact}", flush=True)


if __name__ == "__main__":
    main()
