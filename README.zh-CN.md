# Airalogy Masterbrain

English: [README.md](README.md)

Masterbrain 现在采用轻量 monorepo 结构：

```txt
masterbrain/
├── packages/
│   └── masterbrain/  # 发布到 PyPI 的 Python 包、core/provider/API runtime、测试
├── apps/
│   └── studio/       # Vue 3 + TypeScript 独立前端
├── docs/
└── README.zh-CN.md
```

`masterbrain` 按运行时依赖不同的基础包：backend 依赖已发布的 `airalogy` Python 包，frontend 依赖已发布的 `@airalogy/aimd-*` npm 包。桌面版 Masterbrain 已支持把 `.aira` 归档导入本地 SQLite library，在 UI 中浏览导入的 protocol 和 record，并在需要时把某个 protocol 一键重新装载到当前 workspace。

关于 `masterbrain`、`airalogy`、`aimd` 三者的仓库关系、本地联调方式，以及跨 repo 的 release 顺序，见 [`CONTRIBUTING.zh-CN.md`](./CONTRIBUTING.zh-CN.md)。
当前的平台覆盖范围和打包限制见 [`PLATFORM_SUPPORT.zh-CN.md`](./PLATFORM_SUPPORT.zh-CN.md)。
PyPI 自动发布流程见 [`RELEASING.zh-CN.md`](./RELEASING.zh-CN.md)。

## 快速开始

先构建一次前端：

```shell
npm install
npm --prefix apps/studio install
npm run studio:build
```

先在 `packages/masterbrain/.env` 中配置 Python 包运行环境变量：

```shell
cd packages/masterbrain
cp .env.example .env
```

按需填写 `DASHSCOPE_API_KEY`、`OPENAI_API_KEY` 等配置后，再初始化后端并启动一体化本地应用：

```shell
cd packages/masterbrain
uv sync
uv run masterbrain-studio
```

这会启动一个本地进程，同时提供后端 API 和已构建的 Web UI，并自动在默认浏览器中打开 Masterbrain。

`uv run masterbrain-desktop` 仅作为废弃的兼容别名保留，未来版本会移除。

如果你要直接绑定某个工作目录启动：

```shell
uv run masterbrain-studio --workspace /path/to/project
```

如果你想让 Masterbrain 直接打开一个 `.aira` 文件并先导入本地库：

```shell
uv run masterbrain-studio /path/to/archive.aira
```

源代码运行模式下，对话改代码功能仍然需要 OpenCode runtime。你可以把 `opencode` 放到系统 `PATH`，或者执行：

```shell
python3 scripts/vendor_opencode.py
```

## 开发模式

在 `packages/masterbrain` 中启动 FastAPI 服务：

```shell
cd packages/masterbrain
uv sync --dev
uv run uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

在仓库根目录启动 Studio 前端：

```shell
npm --prefix apps/studio install
npm run studio:dev
```

Vite 开发服务器默认运行在 `http://localhost:5173`，并将 `/api/*` 代理到 `http://127.0.0.1:8080`。

## 打包

PyPI 发布由 GitHub Actions 在推送 `v*` tag 时自动执行。完整流程见 [`RELEASING.zh-CN.md`](./RELEASING.zh-CN.md)。

在 `packages/masterbrain` 中构建本地桌面包：

```shell
cd packages/masterbrain
uv run masterbrain-build-desktop
```

也保留了平台封装脚本：

- macOS / Linux：`./scripts/build_desktop_bundle.sh`
- Windows PowerShell：`.\scripts\build_desktop_bundle.ps1`

该命令会把原始 PyInstaller bundle 输出到 `packages/masterbrain/dist/Masterbrain/`，并同时在 `packages/masterbrain/dist/release/<platform>/` 下生成平台分发物。

- macOS：未签名的 `Masterbrain.app` 与带版本号的 `.zip`
- Windows x64：portable 目录、portable `.zip`、Inno Setup `.iss` 安装器脚本；如果本机可用 `ISCC.exe`，会自动额外生成安装器 `.exe`
- Linux：portable 目录与带版本号的 `.tar.gz`

## 测试

在 `packages/masterbrain` 中运行 Python 包测试：

```shell
cd packages/masterbrain
uv run python -m pytest
```

`packages/masterbrain/pytest.ini` 默认会跳过依赖外部 API 的测试标记。

## 应用文档

- Python 包：[packages/masterbrain/README.md](packages/masterbrain/README.md)
- Studio 前端：[apps/studio/SETUP.md](apps/studio/SETUP.md)

## 文档站

在仓库根目录运行 VitePress 文档站：

```shell
npm install
npm run docs:dev
```

构建静态站点：

```shell
npm run docs:build
```

## 引用

如果 Airalogy Masterbrain 对你的研究或项目有帮助，欢迎引用以下论文：

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
