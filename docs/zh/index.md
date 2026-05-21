---
layout: home

hero:
  name: Airalogy Masterbrain
  text: 科研自动化的中央智能
  tagline: Masterbrain 是科研流程的主脑与智能中枢，统一协调研究规划、工具调用与执行。
  actions:
    - theme: brand
      text: 快速开始
      link: /zh/quickstart
    - theme: alt
      text: 系统架构
      link: /zh/ai-architecture
    - theme: alt
      text: Endpoint 总览
      link: /zh/endpoints/

features:
  - title: 一体化本地应用
    details: 前端构建一次后，可以直接以桌面式本地应用启动，并绑定真实目录进行编辑。
  - title: 明确的后端契约
    details: 每个 endpoint 都维护自己的输入输出模型，便于前后端协作，也便于 AI 工作流扩展。
  - title: 可扩展的 AI 工具链
    details: Protocol 生成、字段录入、Record QA 和 AIRA 都建立在统一的工具调用与工作流设计之上。
---

Masterbrain 采用轻量 monorepo 结构：

```txt
masterbrain/
├── packages/
│   └── masterbrain/  # Python 发布包、core/providers、API runtime、测试
├── apps/
│   └── studio/       # Vue 3 + TypeScript 独立前端
├── docs/      # VitePress 文档站
└── README.zh-CN.md
```

这个文档站用于公开说明仓库结构、运行方式以及几个核心 AI 流程的设计。若你只是想先把项目跑起来，直接从[快速开始](/zh/quickstart)读起。
