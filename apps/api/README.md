# Masterbrain API

Python backend for the Masterbrain monorepo. This app owns the FastAPI service, the desktop launcher, backend tests, and the PyInstaller packaging flow.

The backend now depends directly on the sibling `airalogy` package and uses it to validate and unpack `.aira` archives for the local protocol/record library.

For platform coverage and packaging limits, see [`../../PLATFORM_SUPPORT.md`](../../PLATFORM_SUPPORT.md).

## Setup

```shell
cp .env.example .env
uv sync --dev
```

If you prefer to keep a repo-root `.env`, the backend still loads it as a fallback, but `apps/api/.env` is now the standard location.

## Run

Start the FastAPI server:

```shell
uv run uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

Launch the integrated desktop-style local app after building the frontend in `apps/web`:

```shell
uv run masterbrain-desktop
```

You can bind the app to an existing workspace directory:

```shell
uv run masterbrain-desktop --workspace /path/to/project
```

You can also pass an `.aira` archive path as the launch document. Masterbrain will import it into the local library before opening the UI:

```shell
uv run masterbrain-desktop /path/to/archive.aira
```

## OpenCode

Code-edit flows require an OpenCode runtime. Either install `opencode` globally, or vendor it locally:

```shell
python3 scripts/vendor_opencode.py
```

## Tests

Run the backend test suite:

```shell
uv run python -m pytest
```

`pytest.ini` excludes `openai` and `qwen` markers by default.

## Packaging

Build the packaged local bundle with the cross-platform CLI:

```shell
uv run masterbrain-build-desktop
```

Wrapper scripts are also available:

- macOS / Linux: `./scripts/build_desktop_bundle.sh`
- Windows PowerShell: `.\scripts\build_desktop_bundle.ps1`

This builds the frontend from `apps/web`, vendors OpenCode into `apps/api/vendor/`, syncs the packaging dependency group, writes the raw PyInstaller bundle to `apps/api/dist/Masterbrain/`, and then packages platform release artifacts under `apps/api/dist/release/<platform>/`.

- macOS: unsigned `Masterbrain.app` and a versioned `.zip`
- Windows x64: portable directory, portable `.zip`, and an Inno Setup `.iss` script; if `ISCC.exe` is available or passed via `--inno-setup-compiler`, the installer `.exe` is also built
- Linux: portable directory and a versioned `.tar.gz`
