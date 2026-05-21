# 代码结构

Masterbrain 采用轻量 monorepo 结构：

```txt
masterbrain/
├── packages/
│   └── masterbrain/
│       ├── pyproject.toml
│       ├── src/masterbrain/
│       └── tests/
├── apps/
│   └── studio/
│       ├── src/
│       └── package.json
├── docs/
└── README.zh-CN.md
```

本页重点说明 `packages/masterbrain/src/masterbrain/` 下的 Python 发布包组织方式。

## Python 包分层

Python 包现在围绕稳定的 core/provider/API 边界组织：

- `core/`：与模型供应商无关的 AI 契约、事件和请求类型，以及后续无状态 workflow
- `providers/`：OpenAI-compatible、Qwen/DashScope 等具体模型供应商适配和模型路由
- `endpoints/`：FastAPI endpoint 契约和应用层编排
- `fastapi/`：可部署 HTTP 应用的装配层

下游应用应依赖这个 Python 包或它暴露的 HTTP API，不依赖 Masterbrain Studio 前端。

## Endpoint 优先的组织方式

Masterbrain 的大部分 AI 能力都按 endpoint 组织。一个 endpoint 一般包含：

- `types.py` 或 `types/`：输入输出数据模型
- `router.py`：FastAPI 路由
- `logic/`：业务逻辑实现

典型结构如下：

```txt
masterbrain/endpoints/
├── <endpoint_name>/
│   ├── router.py
│   ├── types.py
│   └── logic/
│       ├── __init__.py
│       └── ...
```

对于多级 endpoint，目录结构可以直接映射 URL 结构，例如：

```txt
masterbrain/endpoints/
├── chat/
│   ├── field_input/
│   └── qa/
│       ├── language/
│       ├── stt/
│       └── vision/
├── protocol_generation/
│   ├── aimd/
│   ├── assigner/
│   └── model/
```

## 为什么强调 `types`

`types` 层是公共契约，而不是附属细节。这样做有几个直接收益：

- 前端可以先对接数据结构，再深入业务逻辑
- 每个 endpoint 可以独立约束支持的模型
- 校验集中在入口边界，而不是散落在实现内部
- 测试可以围绕稳定的 payload 结构构建

## FastAPI 主入口

`masterbrain/fastapi/main.py` 负责：

- 创建 FastAPI 应用
- 配置本地开发需要的 CORS
- 注册所有 endpoint 路由
- 统一处理模型相关异常
- 在前端构建产物存在时直接托管 `apps/studio/dist`

## 当前主要后端模块

- `core/`：无状态、供应商无关的 AI 契约
- `providers/`：模型供应商适配与模型到供应商的路由
- `endpoints/`：用户可见的 API 路由与业务逻辑
- `prompts/`：系统消息与 prompt 资源
- `utils/`：LLM 集成、打印、OpenCode 等辅助逻辑
- `workspace_manager.py`：目录工作区状态和文件操作
- `desktop.py`：本地桌面式启动入口

## 测试

Python 测试位于 `packages/masterbrain/tests/`，大多按 endpoint 维度组织。这让“API 契约 -> 实现 -> 测试覆盖”之间的映射关系比较清晰。Studio 前端检查位于 `apps/studio`。
