# Contributing

中文说明：[`CONTRIBUTING.zh-CN.md`](./CONTRIBUTING.zh-CN.md)

## Repo Relationship

`masterbrain`, `airalogy`, and `aimd` are separate open-source repositories with different responsibilities:

- `airalogy` is the Python package for protocol, record, and archive primitives such as `.aira`.
- `aimd` is the TypeScript package set for AIMD-related frontend/runtime implementations.
- `masterbrain` is the end-user application layer that consumes them.

The intended repository model is:

- keep all three as separate repos
- `masterbrain` backend depends on `airalogy`
- `masterbrain` frontend depends on published `@airalogy/aimd-*` npm packages
- `airalogy` and `aimd` do not depend on each other as packages
- local sibling checkouts can be used as a convenient working-copy layout for cross-repo validation

## Working Copy Layout

For cross-repo development, you can keep the repos as sibling directories:

```txt
workspace/
├── airalogy/
├── aimd/
└── masterbrain/
```

This layout is only a contributor convenience for opening and validating multiple repos together. Masterbrain Studio must depend on published `@airalogy/aimd-*` npm packages and should not default to Vite aliases or source paths from a sibling `aimd/` checkout.

## Dependency Policy

Use two different modes deliberately:

### 1. Published Dependency Mode

Use this for releases and for any setup that should work without a sibling checkout.

- `masterbrain` backend should depend on a published `airalogy` version.
- `masterbrain` frontend should depend on published `aimd` packages.
- When `airalogy` is still evolving quickly, prefer pinning to an exact version.
- Apply the same versioning discipline to `aimd` packages used by the frontend.
- Only relax version ranges after the relevant API surface becomes stable.

### 2. Local Joint-Development Mode

Use this when developing `masterbrain` together with `airalogy` and/or `aimd`.

- clone the relevant repos side by side
- edit `airalogy` for backend-facing changes
- edit `aimd` for frontend-facing AIMD changes
- build and validate the package in `aimd`; if you need to test unpublished frontend changes inside `masterbrain`, use temporary local npm link/pack workflows, but do not commit local path dependencies or Vite aliases
- only merge `masterbrain` work after the required dependency changes are ready

This mode is for contributor velocity. It should not become the only install path for downstream users.

## Cross-Repo Change Workflow

When a `masterbrain` feature requires dependency changes:

### Backend-facing change

1. Implement and validate the lower-level change in `airalogy`.
2. Update `masterbrain` backend to use the new behavior through the local sibling checkout.
3. Run local tests in both repos.
4. Release or otherwise publish the required `airalogy` version.
5. Update `masterbrain` to point at that released `airalogy` version.
6. Merge the `masterbrain` change after the dependency boundary is explicit again.

### Frontend-facing change

1. Implement and validate the required AIMD change in `aimd`.
2. If needed, temporarily validate the unpublished package locally with npm link/pack, without committing local path dependencies.
3. Run local frontend checks in both repos.
4. Release or otherwise publish the required `aimd` package version.
5. Update `masterbrain` frontend dependency metadata and lockfile.
6. Merge the `masterbrain` change after the dependency boundary is explicit again.

Avoid merging `masterbrain` code that only works against unpublished dependency states unless that coupling is intentionally temporary and clearly documented.

## API Boundary Rules

Treat both `airalogy` and `aimd` as package dependencies, not as internal source trees.

- Prefer importing documented, intentional APIs from `airalogy`.
- Prefer using the shared `aimd` implementation on the frontend instead of maintaining parallel AIMD logic in `masterbrain`.
- Do not reach into private implementation details unless you are prepared to stabilize them.
- If `masterbrain` needs a backend capability repeatedly, add or refine the API in `airalogy` instead of duplicating `.aira` or protocol logic inside `masterbrain`.
- If `masterbrain` needs a frontend AIMD capability repeatedly, add or refine it in `aimd` instead of keeping a divergent local implementation.

## Release Checklist

For changes that span repos:

1. Confirm the required `airalogy` and/or `aimd` change is merged.
2. Cut the needed dependency release.
3. Update `masterbrain` dependency metadata and lockfiles.
4. Re-run `masterbrain` backend tests and frontend build.
5. Document any required upgrade notes in the changelog.

## Commands

Typical local commands in `masterbrain`:

```bash
cd packages/masterbrain
uv sync --dev
uv run python -m pytest
```

```bash
cd apps/studio
npm install
npm run build
```

Use `uv run python -m pytest` instead of `uv run pytest` in this repo so the Python module path is resolved consistently with the local dependency layout.
