# Masterbrain Studio — Environment Setup

## Prerequisites

| Tool | Required Version |
|------|-----------------|
| Node.js | >= 18 |
| npm | >= 9 |
| Python | >= 3.13 |
| uv | latest |
| OpenCode CLI | latest, for source/dev runs |

Studio depends on the published `@airalogy/aimd-*` npm packages for AIMD editor, renderer, and preview styles. A sibling `aimd/` checkout is not required for normal source builds.

---

## 1. Backend

```bash
cd packages/masterbrain

# Install Python dependencies
uv sync

# Install OpenCode runtime for source/dev runs (choose one)
curl -fsSL https://opencode.ai/install | bash
# or: brew install anomalyco/tap/opencode
# or: python3 scripts/vendor_opencode.py

# Start the API server (http://127.0.0.1:8080)
uv run uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

> The backend must be running before the frontend dev server starts, otherwise API proxy calls will fail.
>
> In source and development mode, the OpenCode-backed code editing flow shells out to a local `opencode` binary from the FastAPI backend. Make sure `opencode` is on your `PATH`, or vendor it with `python3 scripts/vendor_opencode.py`.

## Recommended Local App Mode

For regular local use, build the frontend once and launch Masterbrain as a single local app:

```bash
# 1. Build the frontend
cd apps/studio
npm install
npm run build

# 2. Start the integrated app from packages/masterbrain
cd ../../packages/masterbrain
uv run masterbrain-studio
```

This starts the FastAPI backend, serves the built web UI from the same process, and opens Masterbrain in your default browser automatically.

`masterbrain-desktop` is kept as a deprecated compatibility alias and will be removed in a future release.

Masterbrain now uses a real local workspace directory as the primary editing model. You can choose a folder from the sidebar, paste a path into the sidebar, or start directly against a directory:

```bash
uv run masterbrain-studio --workspace /path/to/project
```

Edits made in the UI are written directly to that directory on disk.
ZIP imports are unpacked directly into the selected workspace directory by the backend, and ZIP exports are generated directly from that directory as well.

When you run from source, this mode expects OpenCode to already be available on `PATH` or vendored locally. You do not need to start OpenCode manually. If `opencode` is already installed, you can launch directly with `uv run masterbrain-studio`; Masterbrain will invoke the local `opencode` binary automatically when code editing is requested. If you just want to verify the installation, run `opencode --version`. When you run the packaged desktop bundle, OpenCode is bundled automatically.

## Desktop Bundle Scaffold

If you want a distributable local app bundle, use:

```bash
cd packages/masterbrain
uv run masterbrain-build-desktop
```

This uses PyInstaller, automatically downloads and bundles the matching OpenCode CLI, writes the raw bundle to `packages/masterbrain/dist/Masterbrain/`, and then prepares release artifacts under `packages/masterbrain/dist/release/<platform>/`.
On macOS/Linux you can still use `./scripts/build_desktop_bundle.sh`, and on Windows PowerShell you can use `.\scripts\build_desktop_bundle.ps1`.

- macOS: unsigned `Masterbrain.app` plus a versioned `.zip`
- Windows x64: portable directory, portable `.zip`, and an Inno Setup `.iss` installer script; if `ISCC.exe` is present, the installer `.exe` is built too
- Linux: portable directory plus a versioned `.tar.gz`

---

## 2. Frontend

```bash
cd apps/studio

npm install

# Start dev server (http://localhost:5173)
npm run dev
```

The Vite dev server proxies all `/api/*` requests to `http://127.0.0.1:8080`, so no CORS configuration is needed during development.
It resolves AIMD editor/renderer runtime files from the installed `@airalogy/aimd-*` npm packages.

This mode is mainly for frontend development. For normal local use, prefer `masterbrain-studio`.

---

## 3. Key Dependencies

| Package | Purpose |
|---------|---------|
| `vue` | UI framework (Vue 3 Composition API) |
| `monaco-editor` | Code editor host for `.aimd` / Python files |
| `@airalogy/aimd-editor` | AIMD Monaco grammar and editor integration |
| `@airalogy/aimd-renderer` | AIMD HTML preview renderer and styles |
| `@airalogy/aimd-recorder` | Shared AIMD record/preview styles used by Studio |
| `markdown-it` | Render AI chat messages as Markdown |
| `tailwindcss` | Utility-first CSS (class-based dark mode via `darkMode: 'class'`) |

---

## 4. Available Scripts

```bash
npm run dev          # Start dev server
npm run build        # Type-check + production build
npm run type-check   # vue-tsc type checking only
npm run lint         # ESLint
npm run preview      # Preview production build
```

---

## 5. Production Build

```bash
cd apps/studio
npm run build
# Output: apps/studio/dist/
```

The FastAPI backend now serves the built files in `apps/studio/dist/` automatically when they exist, including in `masterbrain-studio` mode.

---

## 6. Environment Variables

Create a `.env` file in `packages/masterbrain/` (next to `pyproject.toml`) if needed:

```env
OPENAI_API_KEY=sk-...
DASHSCOPE_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

Notes:

- `DASHSCOPE_API_KEY` is required if you use the default Qwen models for OpenCode-backed code editing.
- `OPENAI_API_KEY` is required if you switch the code-edit runtime to a GPT model in the future.

---

## 7. Project Structure

```txt
masterbrain/
├── packages/
│   └── masterbrain/
│       ├── pyproject.toml
│       ├── src/masterbrain/
│       │   ├── core/
│       │   ├── providers/
│       │   ├── endpoints/
│       │   └── fastapi/
│       └── tests/
├── apps/
│   └── studio/
│       ├── package.json
│       ├── vite.config.ts
│       └── src/
│           ├── main.ts
│           ├── App.vue
│           ├── composables/
│           ├── components/
│           ├── types/
│           └── utils/
└── docs/
```
