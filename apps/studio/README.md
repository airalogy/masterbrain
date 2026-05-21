# Masterbrain Studio

Vue 3 + TypeScript + Vite standalone frontend for the Masterbrain Python API.

## Quick Start

```bash
cd apps/studio
npm install
npm run dev  # → http://localhost:5173
```

The Vite dev server proxies all `/api/*` requests to `http://127.0.0.1:8080`.

Start the backend from `packages/masterbrain` before launching the frontend. See [SETUP.md](./SETUP.md) for the full monorepo workflow.

## Build

```bash
npm run build  # Output: dist/
```
