# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files


spec_dir = Path(globals().get("__file__", Path(globals().get("SPECPATH", Path.cwd())))).resolve()
if spec_dir.is_file():
    spec_dir = spec_dir.parent

api_root = spec_dir.parents[1]
web_dist = api_root.parent / "web" / "dist"
vendored_opencode = api_root / "vendor" / "opencode"
package_data = collect_data_files(
    "masterbrain",
    includes=["**/*.md", "**/*.json", "**/*.txt"],
)

if not web_dist.exists():
    raise SystemExit(
        "Frontend build not found. Run `npm run build` inside `apps/web` before packaging."
    )

if not vendored_opencode.exists():
    raise SystemExit(
        "Vendored OpenCode not found. Run `python3 scripts/vendor_opencode.py` before packaging."
    )


a = Analysis(
    [str(api_root / "src" / "masterbrain" / "desktop.py")],
    pathex=[str(api_root / "src")],
    binaries=[],
    datas=[
        (str(web_dist), "web_dist"),
        (str(vendored_opencode), "vendor/opencode"),
        *package_data,
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Masterbrain",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Masterbrain",
)
