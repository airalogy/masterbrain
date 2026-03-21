# Airalogy Masterbrain

简体中文：[README.zh-CN.md](README.zh-CN.md)

[Setup](#-setup) • [Features](#-features) • [API Documentation](#-api-documentation)

## 🚀 Setup

Airalogy Masterbrain API is deployed locally using FastAPI. You need to start the FastAPI service before calling the API.

### Recommended: run as a single local app

For regular local use, especially for non-developers, the preferred mode is:

```shell
# Build the web UI once
cd src/web
npm install
npm run build

# Return to the project root and launch the integrated local app
cd ../..
uv sync
uv run masterbrain-desktop
```

This starts one local process that serves both the backend API and the built web UI, then opens Masterbrain in your default browser automatically.

Masterbrain now uses a real local workspace directory as its primary editing model. After launch, you can either:

- choose a folder from the left sidebar inside the app,
- paste a directory path into the sidebar and open it, or
- pass a workspace path on startup:

```shell
uv run masterbrain-desktop --workspace /path/to/project
```

Files created, edited, renamed, or deleted in the UI are written directly to that directory on disk.
ZIP imports are unpacked directly into the selected workspace directory, and ZIP exports are produced directly from that directory on the backend.

For source checkouts, chat-driven code editing still needs an OpenCode runtime.

If `opencode` is already installed on your machine, you do not need to start a separate `opencode` service manually. As long as the `opencode` command is available on `PATH`, and you have already completed the frontend build and `uv sync` steps above, you can launch Masterbrain directly with:

```shell
uv run masterbrain-desktop
```

Masterbrain will invoke the local `opencode` binary automatically when chat-driven code editing is needed, using short-lived `opencode serve` processes internally.

If you only want to verify that `opencode` is installed correctly, run:

```shell
opencode --version
```

If not, either install it globally:

```shell
curl -fsSL https://opencode.ai/install | bash
```

or vendor the official binary into this repo:

```shell
python3 scripts/vendor_opencode.py
```

### Packaging direction

The project now also includes a packaging scaffold for a desktop-style local bundle:

```shell
./scripts/build_desktop_bundle.sh
```

This builds the frontend, downloads and bundles the matching OpenCode CLI, syncs the Python packaging toolchain, and creates a PyInstaller bundle under `dist/Masterbrain/`.

End users running the packaged bundle do not need to install `opencode` separately.

### 1. Install `uv`

Install `uv` locally before continuing.

### 2. Sync dependencies with `uv`

```shell
# Production mode
uv sync

# Development mode (including pytest, etc.)
uv sync --dev
```

### 3. Set up environment variables

Copy the `.env.example` file to `.env` and configure it according to the instructions.

```shell
cp .env.example .env
```

### 4. Start the FastAPI service

```shell
# Production mode
uv run uvicorn masterbrain.fastapi.main:app --host 127.0.0.1 --port 8080

# Development mode
uv run uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

You can modify the port according to your needs.

### 5. Start the web frontend

If you want to use the interactive web UI, start the frontend after the FastAPI service is running.

Requirements:

- Node.js >= 18
- npm >= 9

```shell
cd src/web

# Install frontend dependencies
npm install

# Start Vite dev server
npm run dev
```

Default frontend address:

- `http://localhost:5173`

During development, the Vite dev server proxies `/api/*` requests to `http://127.0.0.1:8080`.

This split frontend/backend mode is primarily for development. For day-to-day local usage, prefer the integrated `masterbrain-desktop` launcher. In development mode, OpenCode still needs to be available from `PATH` or vendored locally with `python3 scripts/vendor_opencode.py`.

### 6. Build the web frontend

```shell
cd src/web
npm run build
```

Build output:

- `src/web/dist/`

## 🧩 Features

Masterbrain API provides the following main feature modules:

### Chat Features

- **Standard Chat**: `/api/endpoints/chat/qa/language` - Provides basic chat functionality
- **Workspace**: `/api/endpoints/workspace` - Selects and manages the real local workspace directory used by the app, including ZIP import/export against that directory
- **Code Edit**: `/api/endpoints/code_edit` - Materializes the current workspace snapshot into a temporary project directory and delegates code edits to a local OpenCode runtime
- **Vision**: `/api/endpoints/chat/qa/vision` - Supports image processing and analysis
- **Speech-to-Text**: `/api/endpoints/chat/qa/stt` - Supports voice input conversion to text
- **Field Input**: `/api/endpoints/chat/field_input` - Structured field input processing

### Protocol Generation

- **AIMD Protocol**: `/api/endpoints/protocol_generation/aimd` - AI model-driven protocol generation
- **Model Protocol**: `/api/endpoints/protocol_generation/model` - Model-related protocol generation
- **Assigner Protocol**: `/api/endpoints/protocol_generation/assigner` - Task assignment protocol generation
- **Single File**: `/api/endpoints/single_protocol_file_generation` - Single protocol file generation

### Protocol Check & Debug

- **Protocol Check**: `/api/endpoints/protocol_check` - Validates protocol validity
- **Protocol Debug**: `/api/endpoints/protocol_debug` - Protocol debugging tools

### AIRA Workflow

- **AIRA**: `/api/endpoints/aira` - AIRA integration workflow

### Paper Generation

- **Paper Generation**: `/api/endpoints/paper_generation` - Paper generation

## 📚 API Documentation

After starting the service, you can access the API documentation at:

- Default address: `http://127.0.0.1:8080/docs`
- If you modified the Host and Port, please access the corresponding address

## Citation

If you use Airalogy Masterbrain in your research or project, or if this project has been helpful to your work, please cite the following paper:

```bibtex
@misc{yang2025airalogyaiempowereduniversaldata,
      title={Airalogy: AI-empowered universal data digitization for research automation}, 
      author={Zijie Yang and Qiji Zhou and Fang Guo and Sijie Zhang and Yexun Xi and Jinglei Nie and Yudian Zhu and Liping Huang and Chou Wu and Yonghe Xia and Xiaoyu Ma and Yingming Pu and Panzhong Lu and Junshu Pan and Mingtao Chen and Tiannan Guo and Yanmei Dou and Hongyu Chen and Anping Zeng and Jiaxing Huang and Tian Xu and Yue Zhang},
      year={2025},
      eprint={2506.18586},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2506.18586}, 
}
```
