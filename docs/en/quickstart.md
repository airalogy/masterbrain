# Quick Start

## Prerequisites

- Node.js `>= 18`
- npm `>= 9`
- Python `>= 3.13`
- `uv`
- OpenCode CLI for source and development mode code editing

## Run the integrated local app

Build the frontend once:

```sh
cd apps/studio
npm install
npm run build
```

Then start the Python package in Studio mode:

```sh
cd ../../packages/masterbrain
cp .env.example .env
uv sync
uv run masterbrain-studio
```

This starts one local process that serves the FastAPI backend and the built web UI, then opens Masterbrain in your default browser.

`uv run masterbrain-desktop` is kept as a deprecated compatibility alias and will be removed in a future release.

If you want to open a specific directory immediately:

```sh
uv run masterbrain-studio --workspace /path/to/project
```

## Development mode

Backend:

```sh
cd packages/masterbrain
uv sync --dev
uv run uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

Frontend:

```sh
cd apps/studio
npm install
npm run dev
```

The Vite dev server runs at `http://localhost:5173` and proxies `/api/*` to `http://127.0.0.1:8080`.

## Environment variables

Create `packages/masterbrain/.env` when needed:

```ini
OPENAI_API_KEY=sk-...
DASHSCOPE_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

Notes:

- `DASHSCOPE_API_KEY` is required for the default Qwen-based code-edit runtime.
- `OPENAI_API_KEY` is required for OpenAI-backed endpoints and future GPT-based code-edit flows.

## Tests

Run Python package tests from `packages/masterbrain`:

```sh
uv run pytest
```

`packages/masterbrain/pytest.ini` skips API-backed markers by default.
