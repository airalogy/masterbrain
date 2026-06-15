# 发布

[English Version](RELEASING.md)

Masterbrain 会在推送类似 `v0.8.1` 的版本标签时，通过 GitHub Actions 自动把 `masterbrain` Python 包发布到 PyPI。

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

`packages/masterbrain/pyproject.toml` 是当前仓库中唯一硬编码维护包版本号的位置。

## PyPI 配置

要让自动发布成功，需要在 PyPI 项目中将 `YANG-Zijie/masterbrain` 的 `.github/workflows/release.yml` 配置为受信任发布者。

这项配置通常只需要做一次：

- Owner：`YANG-Zijie`
- Repository：`masterbrain`
- Workflow：`.github/workflows/release.yml`
- Environment：`pypi`

## 说明

- 普通功能开发不应修改版本号或 changelog，除非当前改动就是明确的 release preparation。
- Git tag、两份 changelog 条目和 `packages/masterbrain/pyproject.toml` 中的版本号应保持一致。
- `CHANGELOG.md` 是默认英文版；`CHANGELOG.zh-CN.md` 是中文版，两者需要同步维护。
- PyPI workflow 只发布 `packages/masterbrain` 下的 Python 包；Studio 前端不会作为独立 npm 包上传到 PyPI。
