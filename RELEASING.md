# Releasing

[中文版本](RELEASING.zh-CN.md)

Masterbrain has independent Python and npm release tracks. The `masterbrain` Python package is published to PyPI when a `v*` tag is pushed. The public npm packages are versioned and published with Changesets from `main`.

## Release Flow

1. Update the package version in `packages/masterbrain/pyproject.toml`.
2. Add matching top entries to `CHANGELOG.md` and `CHANGELOG.zh-CN.md`.
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

`packages/masterbrain/pyproject.toml` is the Python version source. It is independent from npm package versions.

## npm packages and Changesets

Feature and fix changes to `@airalogy/masterbrain-client` or `@airalogy/masterbrain-vue` must include a file under `.changeset/`. Do not edit their versions or generated package changelogs by hand.

After a change reaches `main`, `.github/workflows/release-npm.yml` opens or updates the version PR. Merging that PR publishes the changed packages to npm with GitHub Actions provenance.

Both public packages use npm Trusted Publishing instead of a long-lived write token. Their npm settings must trust GitHub Actions from organization `airalogy`, repository `masterbrain`, and workflow `release-npm.yml`, with `npm publish` allowed. Keep the optional environment name empty unless the workflow is also updated to use that GitHub environment. After the trust relationship is verified, select npm's restrictive publishing-access option that requires two-factor authentication and disallows bypass-2FA tokens.

The GitHub repository must allow Actions to create pull requests while its default workflow permission can remain read-only. The workflow grants only the explicit `contents`, `pull-requests`, and `id-token` permissions it needs.

The version command also synchronizes the root npm lockfile after Changesets updates package versions, so the generated release PR remains compatible with `npm ci`.

Useful local checks:

```bash
npm run packages:type-check
npm run packages:test
npm run studio:build
```

## PyPI Setup

PyPI must trust `airalogy/masterbrain` with workflow file `.github/workflows/release.yml` for publishing to succeed.

Configure this once in the PyPI project settings:

- Owner: `airalogy`
- Repository: `masterbrain`
- Workflow: `.github/workflows/release.yml`
- Environment: `pypi`

## Notes

- Normal feature work should not bump versions or edit changelogs unless it is explicitly release preparation.
- Keep the intended Git tag, both changelog entries, and the version in `packages/masterbrain/pyproject.toml` aligned.
- `CHANGELOG.md` is the default English changelog; `CHANGELOG.zh-CN.md` is the Chinese version and should be kept in sync.
- The PyPI workflow publishes only the Python package under `packages/masterbrain`.
- The npm workflow publishes only `packages/client` and `packages/vue`; Studio remains private and is never published.
- Do not restore `NPM_TOKEN` or `NODE_AUTH_TOKEN` for publishing. OIDC provides a short-lived credential bound to the trusted repository and workflow.
