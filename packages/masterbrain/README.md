# Masterbrain Python Package

Published Python package for the Masterbrain monorepo. It owns the provider-neutral AI core, model provider adapters, FastAPI service, desktop launcher, Python tests, and PyInstaller packaging flow.

The package depends on the sibling `airalogy` package in source checkouts and uses it to validate and unpack `.aira` archives for the local protocol/record library.

For platform coverage and packaging limits, see [`../../PLATFORM_SUPPORT.md`](../../PLATFORM_SUPPORT.md).
For PyPI release automation, see [`../../RELEASING.md`](../../RELEASING.md).

## Setup

```shell
cp .env.example .env
uv sync --dev
```

`packages/masterbrain/.env` is the standard location for local runtime configuration.

## Run

Start the FastAPI server:

```shell
uv run uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

Launch the integrated desktop-style local app after building the frontend in `apps/studio`:

```shell
uv run masterbrain-studio
```

`masterbrain-desktop` is kept as a deprecated compatibility alias and will be removed in a future release.

You can bind the app to an existing workspace directory:

```shell
uv run masterbrain-studio --workspace /path/to/project
```

You can also pass an `.aira` archive path as the launch document. Masterbrain will import it into the local library before opening the UI:

```shell
uv run masterbrain-studio /path/to/archive.aira
```

## OpenCode

Code-edit flows require an OpenCode runtime. Either install `opencode` globally, or vendor it locally:

```shell
python3 scripts/vendor_opencode.py
```

## Tests

Run the Python package test suite:

```shell
uv run python -m pytest
```

`pytest.ini` excludes `openai` and `qwen` markers by default.

## Packaging

PyPI publishing is handled by the repository-level GitHub Actions release workflow on `v*` tag pushes.

Build the packaged local bundle with the cross-platform CLI:

```shell
uv run masterbrain-build-desktop
```

Wrapper scripts are also available:

- macOS / Linux: `./scripts/build_desktop_bundle.sh`
- Windows PowerShell: `.\scripts\build_desktop_bundle.ps1`

This builds the frontend from `apps/studio`, vendors OpenCode into `packages/masterbrain/vendor/`, syncs the packaging dependency group, writes the raw PyInstaller bundle to `packages/masterbrain/dist/Masterbrain/`, and then packages platform release artifacts under `packages/masterbrain/dist/release/<platform>/`.

- macOS: unsigned `Masterbrain.app` and a versioned `.zip`
- Windows x64: portable directory, portable `.zip`, and an Inno Setup `.iss` script; if `ISCC.exe` is available or passed via `--inno-setup-compiler`, the installer `.exe` is also built
- Linux: portable directory and a versioned `.tar.gz`
