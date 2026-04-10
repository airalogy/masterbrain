# Platform Support

This document describes the current support level for running and packaging `masterbrain`.

## Support Matrix

| Platform | Source Run | Local Desktop Bundle Build | Bundled OpenCode | Workspace Picker | Status |
|---|---|---|---|---|---|
| macOS Apple Silicon | Yes | Yes | Yes | Yes | Supported |
| macOS Intel | Yes | Yes | Yes | Yes | Supported |
| Windows x64 | Yes | Yes | Yes | Yes | Supported |
| Windows ARM64 | No | No | No | Partial | Not supported |
| Linux x64 | Yes | Yes | Yes | Yes, depends on desktop tools | Supported |
| Linux ARM64 | Yes | Yes | Yes | Yes, depends on desktop tools | Supported |

## What "Supported" Means

- `Source Run` means you can run `uv run masterbrain-desktop` from a source checkout.
- `Local Desktop Bundle Build` means you can build the PyInstaller-based local bundle on that same platform.
- `Bundled OpenCode` means the packaging flow can vendor the official OpenCode CLI for that platform.
- `Workspace Picker` means the UI can ask the OS for a local directory selection dialog.

## Release Artifacts

- macOS builds now emit an unsigned `Masterbrain.app` bundle and a versioned `.zip`.
- Windows x64 builds emit a portable directory, a portable `.zip`, and an Inno Setup `.iss` installer script. If Inno Setup is installed on the build machine, the installer `.exe` is compiled automatically.
- Linux builds emit a portable directory and a versioned `.tar.gz`.

## Important Limits

- Build the desktop bundle on the same target platform. PyInstaller is not being used here as a cross-compiler.
- The current app remains a desktop-style local bundle that opens the browser automatically. macOS builds are not code-signed or notarized, and Windows builds do not currently produce MSI packages.
- Windows support currently assumes `x64`, because the OpenCode runtime vendoring logic only supports `windows-x64`.
- Source builds expect sibling `airalogy/` and `aimd/` repositories next to `masterbrain/`.
- `.aira` file association metadata is now included in the macOS app bundle and the Windows installer script, but OS-level registration still depends on how that artifact is installed or launched.

## Build Entry Points

Preferred cross-platform command:

```shell
cd apps/api
uv run masterbrain-build-desktop
```

Platform wrappers:

- macOS / Linux: `./scripts/build_desktop_bundle.sh`
- Windows PowerShell: `.\scripts\build_desktop_bundle.ps1`
