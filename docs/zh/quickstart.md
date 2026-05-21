# 快速开始

## 前置要求

- Node.js `>= 18`
- npm `>= 9`
- Python `>= 3.13`
- `uv`
- OpenCode CLI：源代码运行和开发模式下的代码编辑依赖它

## 运行一体化本地应用

先构建一次前端：

```sh
cd apps/studio
npm install
npm run build
```

再以 Studio 本地模式启动 Python 包：

```sh
cd ../../packages/masterbrain
cp .env.example .env
uv sync
uv run masterbrain-studio
```

这会启动一个本地进程，同时提供 FastAPI 后端和已构建的 Web UI，并自动在默认浏览器中打开 Masterbrain。

`uv run masterbrain-desktop` 仅作为废弃的兼容别名保留，未来版本会移除。

如果你想启动时直接绑定某个目录：

```sh
uv run masterbrain-studio --workspace /path/to/project
```

## 开发模式

后端：

```sh
cd packages/masterbrain
uv sync --dev
uv run uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

前端：

```sh
cd apps/studio
npm install
npm run dev
```

Vite 开发服务器默认运行在 `http://localhost:5173`，并将 `/api/*` 代理到 `http://127.0.0.1:8080`。

## 环境变量

按需创建 `packages/masterbrain/.env`：

```ini
OPENAI_API_KEY=sk-...
DASHSCOPE_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

说明：

- `DASHSCOPE_API_KEY` 用于默认的 Qwen 代码编辑运行时。
- `OPENAI_API_KEY` 用于 OpenAI 相关 endpoint，以及后续可能切换到 GPT 的代码编辑流程。

## 测试

在 `packages/masterbrain` 中运行：

```sh
uv run pytest
```

`packages/masterbrain/pytest.ini` 默认跳过依赖外部 API 的测试标记。
