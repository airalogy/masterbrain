# Airalogy Masterbrain

简体中文：[README.zh-CN.md](README.zh-CN.md)

Masterbrain now uses a lightweight monorepo layout:

```txt
masterbrain/
├── apps/
│   ├── api/   # FastAPI backend, desktop launcher, packaging, Python tests
│   └── web/   # Vue 3 + TypeScript frontend
├── docs/
└── README.md
```

`masterbrain` is organized to consume separate foundational repos by runtime: the backend depends on `airalogy`, while frontend AIMD behavior is intended to come from `aimd`. The desktop app can import `.aira` archives into a local SQLite library, preview imported protocols and records, and load a stored protocol back into the current workspace when needed.

For the repo relationship, local sibling checkout workflow, and cross-repo release order across `masterbrain`, `airalogy`, and `aimd`, see [`CONTRIBUTING.md`](./CONTRIBUTING.md).
For current platform coverage and packaging limits, see [`PLATFORM_SUPPORT.md`](./PLATFORM_SUPPORT.md).

For source checkouts, the frontend now resolves `@airalogy/aimd-editor/monaco`, `@airalogy/aimd-renderer`, and AIMD preview styles directly from a sibling `aimd/` repository. Keep the local layout as:

```txt
workspace/
├── airalogy/
├── aimd/
└── masterbrain/
```

## Quick Start

Build the frontend once:

```shell
cd apps/web
npm install
npm run build
```

This assumes the sibling `aimd` checkout already exists next to `masterbrain`.

First configure backend environment variables in `apps/api/.env`:

```shell
cd apps/api
cp .env.example .env
```

After filling in `DASHSCOPE_API_KEY`, `OPENAI_API_KEY`, and any other required values, set up the backend and launch the integrated local app:

```shell
cd apps/api
uv sync
uv run masterbrain-desktop
```

This starts one local process that serves both the backend API and the built web UI, then opens Masterbrain in your default browser automatically.

You can also start directly against a workspace directory:

```shell
uv run masterbrain-desktop --workspace /path/to/project
```

Or launch Masterbrain with an `.aira` archive as the initial document:

```shell
uv run masterbrain-desktop /path/to/archive.aira
```

This imports the archive into Masterbrain's local library before the UI opens.

For source checkouts, chat-driven code editing still needs an OpenCode runtime. Either put `opencode` on `PATH`, or vendor it with:

```shell
python3 scripts/vendor_opencode.py
```

Configure backend environment variables in `apps/api/.env`.

## Development

Start the backend from `apps/api`:

```shell
cd apps/api
uv sync --dev
uv run uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

Start the frontend from `apps/web`:

```shell
cd apps/web
npm install
npm run dev
```

The Vite dev server runs at `http://localhost:5173` and proxies `/api/*` to `http://127.0.0.1:8080`.

## Packaging

Build the local desktop bundle from `apps/api`:

```shell
cd apps/api
uv run masterbrain-build-desktop
```

Platform wrappers are also available:

- macOS / Linux: `./scripts/build_desktop_bundle.sh`
- Windows PowerShell: `.\scripts\build_desktop_bundle.ps1`

This writes the raw PyInstaller bundle to `apps/api/dist/Masterbrain/` and also creates platform release artifacts under `apps/api/dist/release/<platform>/`.

- macOS: unsigned `Masterbrain.app` plus a versioned `.zip`
- Windows x64: portable directory, portable `.zip`, and an Inno Setup `.iss` installer script; if `ISCC.exe` is available, the installer `.exe` is built automatically
- Linux: portable directory plus a versioned `.tar.gz`

## Tests

Run backend tests from `apps/api`:

```shell
cd apps/api
uv run python -m pytest
```

`apps/api/pytest.ini` skips API-backed markers by default.

## App Docs

- Backend: [apps/api/README.md](apps/api/README.md)
- Frontend: [apps/web/SETUP.md](apps/web/SETUP.md)

## Documentation Site

Run the VitePress docs site from the repo root:

```shell
npm install
npm run docs:dev
```

Build the static site:

```shell
npm run docs:build
```

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
