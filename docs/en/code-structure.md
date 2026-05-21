# Code Structure

Masterbrain uses a lightweight monorepo layout:

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
└── README.md
```

This page focuses on the published Python package under `packages/masterbrain/src/masterbrain/`.

## Layered Python package

The Python package is now organized around a stable core/provider/API boundary:

- `core/`: provider-neutral AI contracts, event and request types, and future stateless workflows
- `providers/`: concrete model provider selection and SDK adapters such as OpenAI-compatible and Qwen/DashScope clients
- `endpoints/`: FastAPI endpoint contracts and application-specific orchestration
- `fastapi/`: the deployable HTTP application assembly

Downstream applications should depend on this Python package or its HTTP API, not on the Studio frontend.

## Endpoint-first organization

Most backend AI functionality is organized by endpoint. Each endpoint is intended to be a self-contained unit with:

- request and response models in `types.py` or `types/`
- a FastAPI router in `router.py`
- implementation details in `logic/`

Typical structure:

```txt
masterbrain/endpoints/
├── <endpoint_name>/
│   ├── router.py
│   ├── types.py
│   └── logic/
│       ├── __init__.py
│       └── ...
```

For nested endpoint families, the directory structure can mirror the URL structure:

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

## Why the `types` layer matters

The `types` layer is not just implementation detail. It is the contract for callers.

In practice, this gives the project a few benefits:

- frontend code can integrate without reading the full endpoint logic
- supported models can be constrained per endpoint
- validation happens at the boundary instead of being scattered across the logic
- tests can target stable payload shapes

## Main application entry point

The FastAPI application is defined in `masterbrain/fastapi/main.py`.

That module:

- creates the application
- adds CORS middleware for local frontend development
- registers endpoint routers
- normalizes model-related exceptions
- serves the built frontend if present

## Current major backend areas

- `core/`: stateless provider-neutral AI contracts
- `providers/`: model provider adapters and model-to-provider registry
- `endpoints/`: user-facing API routes and business logic
- `prompts/`: reusable prompt files and system message loaders
- `utils/`: helper functions for LLM integration, printing, and OpenCode support
- `workspace_manager.py`: directory-backed workspace state and file operations
- `desktop.py`: local desktop-style launcher entry point

## Tests

Python tests live under `packages/masterbrain/tests/` and mostly mirror the endpoint structure. This makes it easier to reason from public API surface to implementation to test coverage. Studio frontend checks live under `apps/studio`.
