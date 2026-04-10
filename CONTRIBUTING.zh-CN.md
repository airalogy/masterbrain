# 贡献与协作

English version: [`CONTRIBUTING.md`](./CONTRIBUTING.md)

## 仓库关系

`masterbrain`、`airalogy` 和 `aimd` 是三个独立的开源仓库，职责不同：

- `airalogy` 是 Python package，负责 protocol、record、`.aira` 等基础能力。
- `aimd` 是 TypeScript package 集合，负责 AIMD 相关的前端/运行时实现。
- `masterbrain` 是上层应用。

当前采用的仓库组织方式是：

- 保持三个独立 repo
- `masterbrain` backend 依赖 `airalogy`
- `masterbrain` frontend 依赖 `aimd`
- `airalogy` 与 `aimd` 在 package 层面彼此不依赖
- 本地开发时用同级目录联调

## 本地目录结构

本地开发推荐把三个仓库放在同级目录：

```txt
workspace/
├── airalogy/
├── aimd/
└── masterbrain/
```

当前这个 `masterbrain` checkout 已在 backend 侧配置了面向 `uv` 的本地 `airalogy` source override。frontend 侧对 `aimd` 的使用也应遵循同样的 sibling checkout 原则。

## 依赖策略

要明确区分两种模式：

### 1. 正式发布依赖模式

这适用于 release，或者任何不要求用户同时 checkout 两个仓库的环境。

- `masterbrain` backend 应依赖一个已发布的 `airalogy` 版本。
- `masterbrain` frontend 应依赖已发布的 `aimd` package。
- 当 `airalogy` 仍然快速变化时，优先精确 pin 版本。
- frontend 使用的 `aimd` package 也应遵循同样的版本管理纪律。
- 只有在相关 API 稳定后，再放宽版本范围。

### 2. 本地联调模式

这适用于同时开发 `masterbrain` 与 `airalogy` 和/或 `aimd`。

- 相关 repo 同级放置
- backend 相关改动在本地修改 `airalogy`
- frontend 的 AIMD 相关改动在本地修改 `aimd`
- 直接在 `masterbrain` 中联调这些修改
- 只有当所需依赖能力准备好后，再合并 `masterbrain` 侧改动

这种模式是为了提高研发效率，不应该成为下游用户唯一可用的安装方式。

## 跨 Repo 变更流程

当一个 `masterbrain` 功能需要依赖仓库配合修改时：

### backend 相关改动

1. 先在 `airalogy` 实现并验证底层改动。
2. 再在本地 sibling checkout 中更新 `masterbrain` backend 对新能力的使用。
3. 在两个 repo 中分别跑测试。
4. 先发布所需的 `airalogy` 版本。
5. 再把 `masterbrain` 的 backend 依赖更新到这个已发布版本。
6. 最后再合并 `masterbrain`。

### frontend 相关改动

1. 先在 `aimd` 实现并验证所需的 AIMD 改动。
2. 再在本地 sibling checkout 中更新 `masterbrain` frontend 对该实现的使用。
3. 在两个 repo 中分别跑前端检查与构建。
4. 先发布所需的 `aimd` package 版本。
5. 再更新 `masterbrain` frontend 的依赖元数据和 lockfile。
6. 最后再合并 `masterbrain`。

尽量避免把 `masterbrain` 合并到一个只能依赖“尚未发布的依赖源码状态”才能工作的状态，除非这是一个明确标注过的临时开发分支。

## API 边界规则

把 `airalogy` 和 `aimd` 都当作 package dependency，而不是 `masterbrain` 的内部源码目录。

- 优先使用 `airalogy` 中公开、明确的 API。
- frontend 优先直接使用共享的 `aimd` 实现，而不是在 `masterbrain` 中长期维护一套分叉的 AIMD 本地实现。
- 不要默认依赖私有实现细节。
- 如果 `masterbrain` 反复需要 backend 能力，应优先把该能力补到 `airalogy`，而不是在 `masterbrain` 里重复实现 `.aira` 或 protocol 逻辑。
- 如果 `masterbrain` 反复需要 frontend AIMD 能力，应优先把该能力补到 `aimd`，而不是继续保留偏离主实现的本地逻辑。

## 联合发布清单

当一个需求跨越多个 repo 时：

1. 确认所需的 `airalogy` 和/或 `aimd` 改动已经合并。
2. 发布对应的依赖版本。
3. 更新 `masterbrain` 的依赖元数据和 lockfile。
4. 重新运行 `masterbrain` backend 测试和 frontend 构建。
5. 在 changelog 中补充升级说明。

## 常用命令

`masterbrain` 中常用的本地命令：

```bash
cd apps/api
uv sync --dev
uv run python -m pytest
```

```bash
cd apps/web
npm install
npm run build
```

在这个仓库里，推荐使用 `uv run python -m pytest`，而不是 `uv run pytest`，这样在当前本地依赖布局下 Python 模块路径会更稳定。
