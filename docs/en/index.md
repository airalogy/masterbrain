---
layout: home

hero:
  name: Airalogy Masterbrain
  text: Central intelligence for research automation
  tagline: Masterbrain coordinates research planning, tool use, and execution as a unified intelligence layer.
  actions:
    - theme: brand
      text: Quick Start
      link: /en/quickstart
    - theme: alt
      text: Architecture
      link: /en/ai-architecture
    - theme: alt
      text: Endpoint Overview
      link: /en/endpoints/

features:
  - title: Integrated local app
    details: Build the frontend once, launch the backend in desktop mode, and work directly against an existing directory on disk.
  - title: Explicit backend contracts
    details: Each endpoint defines its own request and response models, so frontend integration and AI workflow orchestration stay predictable.
  - title: Extensible AI tooling
    details: Protocol generation, field input, record QA patterns, and AIRA all build on the same tool-calling and workflow concepts.
---

Masterbrain is organized as a lightweight monorepo:

```txt
masterbrain/
├── packages/
│   └── masterbrain/  # Published Python package, core/providers, API runtime, tests
├── apps/
│   └── studio/       # Vue 3 + TypeScript standalone frontend
├── docs/      # VitePress documentation site
└── README.md
```

Use this site for the public-facing, bilingual description of how the repo is structured and how the major AI flows work. For the most direct setup commands, start with [Quick Start](/en/quickstart).
