# 发布

[English Version](RELEASING.md)

Masterbrain 分别管理 Python 和 npm 两条发布线。推送 `v*` 标签时发布 `masterbrain` Python 包到 PyPI；公开 npm 包通过 Changesets 从 `main` 自动版本化并发布。

## 发布流程

1. 更新 `packages/masterbrain/pyproject.toml` 中的包版本。
2. 在 `CHANGELOG.md` 和 `CHANGELOG.zh-CN.md` 顶部补上对应版本条目。
3. 刷新 `packages/masterbrain/uv.lock`，保证 `uv sync --locked --dev` 仍然可用。
4. 将 release-prep 改动合并到 `main`。
5. 推送对应的 Git tag，例如 `git tag v0.8.1 && git push origin v0.8.1`。

发布 workflow 会先校验 Git tag 与 `packages/masterbrain/pyproject.toml` 中的版本是否一致，然后运行 Python release 测试集，构建源码包和 wheel，并通过 Trusted Publishing 发布到 PyPI。

普通 `git push` 默认只会把分支提交推到远端，不会自动创建版本 tag，也不会自动把本地已有 tag 一起推上去。

这个仓库的发布 workflow 监听的是 `v*` 形式的 tag push，而不是分支 push。要触发发布，必须先创建 tag，再显式推送它，例如：

```bash
git tag v0.8.1
git push origin v0.8.1
```

## 版本更新

建议在 `packages/masterbrain` 中使用 `uv version` 更新 `pyproject.toml` 里的 `project.version`，而不是手动改值：

```bash
cd packages/masterbrain
uv version 0.8.1
```

也可以按 SemVer 级别递增：

```bash
cd packages/masterbrain
uv version --bump patch
uv version --bump minor
uv version --bump major
```

`packages/masterbrain/pyproject.toml` 是 Python 版本的唯一来源，与 npm 包版本独立。

## npm 包与 Changesets

修改 `@airalogy/masterbrain-client` 或 `@airalogy/masterbrain-vue` 的功能和修复必须带一份 `.changeset/` 文件，不要手动改版本号或生成的 package changelog。

改动进入 `main` 后，`.github/workflows/release-npm.yml` 会创建或更新版本 PR；合并该 PR 后发布带 GitHub Actions provenance 的 npm 包。

两个公共包使用 npm Trusted Publishing，不保存长期写入 token。npm 包设置必须信任来自 GitHub Actions 的发布：Organization 为 `airalogy`，Repository 为 `masterbrain`，Workflow filename 为 `release-npm.yml`，并允许 `npm publish`。除非 workflow 同时接入对应 GitHub environment，否则 Environment name 保持为空。确认信任关系生效后，应选择 npm 中“要求双因素认证且禁止 bypass-2FA token”的严格发布权限。

GitHub 仓库需要允许 Actions 创建 PR；默认 workflow 权限仍可保持只读，发布 workflow 只显式申请所需的 `contents`、`pull-requests` 与 `id-token` 权限。

版本命令会在 Changesets 更新包版本后同步根目录 npm 锁文件，确保自动生成的版本 PR 仍能通过 `npm ci`。

本地检查：

```bash
npm run packages:type-check
npm run packages:test
npm run studio:build
```

## PyPI 配置

要让自动发布成功，需要在 PyPI 项目中将 `airalogy/masterbrain` 的 `.github/workflows/release.yml` 配置为受信任发布者。

这项配置通常只需要做一次：

- Owner：`airalogy`
- Repository：`masterbrain`
- Workflow：`.github/workflows/release.yml`
- Environment：`pypi`

## 说明

- 普通功能开发不应修改版本号或 changelog，除非当前改动就是明确的 release preparation。
- Git tag、两份 changelog 条目和 `packages/masterbrain/pyproject.toml` 中的版本号应保持一致。
- `CHANGELOG.md` 是默认英文版；`CHANGELOG.zh-CN.md` 是中文版，两者需要同步维护。
- PyPI workflow 只发布 `packages/masterbrain` 下的 Python 包。
- npm workflow 只发布 `packages/client` 和 `packages/vue`；Studio 保持 private，不会发布。
- 不要重新加入用于发布的 `NPM_TOKEN` 或 `NODE_AUTH_TOKEN`；OIDC 会按受信任仓库和 workflow 生成短时凭据。
