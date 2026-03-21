# Airalogy Masterbrain

English: [README.md](README.md)

[安装与设置](#安装与设置) • [功能模块](#功能模块) • [API 文档](#api-文档)

## 安装与设置

Airalogy Masterbrain API 使用 FastAPI 进行本地部署。调用 API 之前，需要先启动 FastAPI 服务。

### 推荐方式：以单一本地应用运行

对于日常本地使用，尤其是面向不熟悉开发环境的用户，推荐使用一体化启动方式：

```shell
# 先构建一次前端界面
cd src/web
npm install
npm run build

# 回到项目根目录后启动一体化本地应用
cd ../..
uv sync
uv run masterbrain-desktop
```

这个模式会启动一个本地进程，同时提供后端 API 和构建后的 Web 界面，并自动在默认浏览器中打开 Masterbrain。

Masterbrain 现在默认以“真实本地目录工作区”作为主要编辑模型。启动后你可以：

- 在应用左侧边栏里直接选择一个文件夹
- 在侧边栏中手动输入目录路径并打开
- 或者在启动时直接指定工作区目录：

```shell
uv run masterbrain-desktop --workspace /path/to/project
```

在界面里创建、修改、重命名、删除的文件，都会直接写回这个磁盘目录。
ZIP 导入会在后端直接解包到当前工作区目录，ZIP 导出也会直接从这个目录打包生成。

如果你是直接运行源码仓库，对话改代码仍然需要 OpenCode runtime。

如果你的机器上已经安装好了 `opencode`，不需要再手动单独启动 `opencode` 服务。只要 `opencode` 命令在系统 `PATH` 中可用，并且已经完成上面的前端构建和 `uv sync`，直接执行下面的命令启动 Masterbrain 即可：

```shell
uv run masterbrain-desktop
```

Masterbrain 会在需要对话改代码时自动调用本机 `opencode` binary，内部按需启动短生命周期的 `opencode serve` 进程。

如果你只是想确认 `opencode` 是否已经安装成功，可以先执行：

```shell
opencode --version
```

如果还没有安装 OpenCode，再二选一：

```shell
curl -fsSL https://opencode.ai/install | bash
```

或者把官方二进制直接下载到仓库里：

```shell
python3 scripts/vendor_opencode.py
```

### 打包方向

项目现在也包含了桌面化本地分发的打包脚手架：

```shell
./scripts/build_desktop_bundle.sh
```

这条命令会构建前端、自动下载并打包匹配平台的 OpenCode CLI、同步 Python 打包依赖，并在 `dist/Masterbrain/` 下生成一个 PyInstaller 本地应用包。

最终给终端用户使用的打包产物不需要额外手动安装 `opencode`。

### 1. 安装 `uv`

开始前，请先在本地安装 `uv`。

### 2. 使用 `uv` 同步依赖

```shell
# 生产环境
uv sync

# 开发环境（包含 pytest 等）
uv sync --dev
```

### 3. 设置环境变量

将 `.env.example` 复制为 `.env`，并按说明完成配置。

```shell
cp .env.example .env
```

### 4. 启动 FastAPI 服务

```shell
# 生产环境
uv run uvicorn masterbrain.fastapi.main:app --host 127.0.0.1 --port 8080

# 开发环境
uv run uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

端口可以根据实际需要调整。

### 5. 启动 Web 前端

如果需要使用交互式 Web 界面，请在 FastAPI 服务启动后再启动前端。

要求：

- Node.js >= 18
- npm >= 9

```shell
cd src/web

# 安装前端依赖
npm install

# 启动 Vite 开发服务器
npm run dev
```

默认前端地址：

- `http://localhost:5173`

开发模式下，Vite 会将 `/api/*` 请求代理到 `http://127.0.0.1:8080`。

这种前后端分离启动方式更适合开发调试。对于日常本地使用，优先使用上面的 `masterbrain-desktop` 一体化启动入口。在开发模式下，OpenCode 仍需要出现在系统 `PATH` 中，或者先执行 `python3 scripts/vendor_opencode.py` 下载到仓库里。

### 6. 构建 Web 前端

```shell
cd src/web
npm run build
```

构建输出目录：

- `src/web/dist/`

## 功能模块

Masterbrain API 提供以下主要功能模块：

### 聊天功能

- **标准聊天**：`/api/endpoints/chat/qa/language` - 提供基础聊天能力
- **工作区管理**：`/api/endpoints/workspace` - 选择并管理应用当前使用的真实本地工作区目录，并支持针对该目录的 ZIP 导入/导出
- **代码编辑**：`/api/endpoints/code_edit` - 将当前工作区快照物化成临时项目目录，并交给本地 OpenCode runtime 执行对话式代码修改
- **视觉功能**：`/api/endpoints/chat/qa/vision` - 支持图像处理与分析
- **语音转文字**：`/api/endpoints/chat/qa/stt` - 支持语音输入转文字
- **字段输入**：`/api/endpoints/chat/field_input` - 提供结构化字段输入处理

### 协议生成

- **AIMD 协议**：`/api/endpoints/protocol_generation/aimd` - AI 模型驱动的协议生成
- **模型协议**：`/api/endpoints/protocol_generation/model` - 模型相关协议生成
- **分配器协议**：`/api/endpoints/protocol_generation/assigner` - 任务分配协议生成
- **单文件生成**：`/api/endpoints/single_protocol_file_generation` - 单协议文件生成

### 协议检查与调试

- **协议检查**：`/api/endpoints/protocol_check` - 校验协议有效性
- **协议调试**：`/api/endpoints/protocol_debug` - 提供协议调试工具

### AIRA 工作流

- **AIRA**：`/api/endpoints/aira` - AIRA 集成工作流

### 论文生成

- **论文生成**：`/api/endpoints/paper_generation` - 论文生成

## API 文档

服务启动后，可以通过以下地址访问 API 文档：

- 默认地址：`http://127.0.0.1:8080/docs`
- 如果修改了 Host 或 Port，请访问对应地址

## 引用

如果您在研究或项目中使用了 Airalogy Masterbrain，或本项目对您的工作有帮助，欢迎引用以下文献：

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
