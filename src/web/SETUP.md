# Web Frontend — Environment Setup

## Prerequisites

| Tool | Required Version |
|------|-----------------|
| Node.js | >= 18 |
| npm | >= 9 |
| Python | >= 3.13 |
| uv | latest |

---

## 1. Backend

```bash
# Install Python dependencies
uv sync

# Start the API server (http://127.0.0.1:8080)
uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

> The backend must be running before the frontend dev server starts, otherwise API proxy calls will fail.

---

## 2. Frontend

```bash
cd src/web

npm install

# Start dev server (http://localhost:5173)
npm run dev
```

The Vite dev server proxies all `/api/*` requests to `http://127.0.0.1:8080`, so no CORS configuration is needed during development.

---

## 3. Key Dependencies

| Package | Purpose |
|---------|---------|
| `vue` | UI framework (Vue 3 Composition API) |
| `monaco-editor` | Code editor with `.aimd` / Python syntax highlighting |
| `jszip` | ZIP upload/download in the browser |
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
cd src/web
npm run build
# Output: src/web/dist/
```

To serve the built files from the FastAPI backend, copy `dist/` to your static files directory and configure FastAPI to serve it.

---

## 6. Environment Variables

Create a `.env` file in the project root (next to `pyproject.toml`) if needed:

```env
OPENAI_API_KEY=sk-...
DASHSCOPE_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

---

## 7. Project Structure

```
masterbrain/
├── pyproject.toml          # Python project config
├── src/
│   ├── masterbrain/        # FastAPI backend
│   │   └── fastapi/
│   │       └── main.py     # API entrypoint
│   └── web/                # Vue 3 frontend
│       ├── package.json
│       ├── vite.config.ts  # Dev proxy: /api → :8080
│       ├── tailwind.config.js
│       └── src/
│           ├── main.ts         # Entry point
│           ├── App.vue         # Root component
│           ├── composables/    # useTheme, useFileManager, useChat
│           ├── components/     # FileManager, EditorPanel, ChatPanel
│           ├── types/          # TypeScript interfaces
│           └── utils/          # apiClient, aimdParser, zipUtils
```
