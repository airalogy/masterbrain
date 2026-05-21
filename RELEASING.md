# Releasing

[中文版本](RELEASING.zh-CN.md)

Masterbrain publishes the `masterbrain` Python package to PyPI from GitHub Actions when a version tag like `v0.8.1` is pushed.

## Release Flow

1. Update the package version in `packages/masterbrain/pyproject.toml`.
2. Add the matching top entry to `CHANGELOG.md`.
3. Refresh `packages/masterbrain/uv.lock` so `uv sync --locked --dev` continues to work.
4. Merge the release-prep change to `main`.
5. Push the matching Git tag, for example `git tag v0.8.1 && git push origin v0.8.1`.

The release workflow validates that the Git tag matches `packages/masterbrain/pyproject.toml`, runs the Python release test set, builds source and wheel distributions, and publishes the package to PyPI through Trusted Publishing.

A normal `git push` only pushes branch commits to the remote. It does not create a version tag, and it does not push existing local tags automatically.

This repository's release workflow listens for `v*` tag pushes, not branch pushes. To trigger a release, create the tag first and then push it explicitly, for example:

```bash
git tag v0.8.1
git push origin v0.8.1
```

## Version Updates

Use `uv version` from `packages/masterbrain` to update `project.version` in `pyproject.toml` instead of editing the value by hand when convenient:

```bash
cd packages/masterbrain
uv version 0.8.1
```

Or bump by SemVer component:

```bash
cd packages/masterbrain
uv version --bump patch
uv version --bump minor
uv version --bump major
```

`packages/masterbrain/pyproject.toml` is the only hardcoded package version source in this repository.

## PyPI Setup

PyPI must trust `YANG-Zijie/masterbrain` with workflow file `.github/workflows/release.yml` for publishing to succeed.

Configure this once in the PyPI project settings:

- Owner: `YANG-Zijie`
- Repository: `masterbrain`
- Workflow: `.github/workflows/release.yml`
- Environment: `pypi`

## Notes

- Normal feature work should not bump versions or edit `CHANGELOG.md` unless it is explicitly release preparation.
- Keep the intended Git tag and `CHANGELOG.md` entry aligned with the version in `packages/masterbrain/pyproject.toml`.
- The PyPI workflow publishes only the Python package under `packages/masterbrain`; Studio frontend artifacts are not uploaded to PyPI as separate npm packages.
