# 平台支持

本文档说明 `masterbrain` 当前在不同平台上的运行与打包支持级别。

## 支持矩阵

| 平台 | 源码运行 | 本地桌面包构建 | 内置 OpenCode | 工作目录选择器 | 状态 |
|---|---|---|---|---|---|
| macOS Apple Silicon | 支持 | 支持 | 支持 | 支持 | 已支持 |
| macOS Intel | 支持 | 支持 | 支持 | 支持 | 已支持 |
| Windows x64 | 支持 | 支持 | 支持 | 支持 | 已支持 |
| Windows ARM64 | 不支持 | 不支持 | 不支持 | 部分可用 | 不支持 |
| Linux x64 | 支持 | 支持 | 支持 | 支持，但依赖桌面环境工具 | 已支持 |
| Linux ARM64 | 支持 | 支持 | 支持 | 支持，但依赖桌面环境工具 | 已支持 |

## “已支持” 的含义

- `源码运行` 指可以在源码 checkout 中执行 `uv run masterbrain-desktop`。
- `本地桌面包构建` 指可以在该平台本机上构建基于 PyInstaller 的本地 bundle。
- `内置 OpenCode` 指打包流程可以自动拉取并随包分发该平台对应的官方 OpenCode CLI。
- `工作目录选择器` 指应用可以调用系统目录选择对话框。

## 分发产物

- macOS 构建现在会生成未签名的 `Masterbrain.app` 和带版本号的 `.zip`。
- Windows x64 构建会生成 portable 目录、portable `.zip` 和 Inno Setup `.iss` 安装器脚本；如果构建机安装了 Inno Setup，还会自动编译安装器 `.exe`。
- Linux 构建会生成 portable 目录和带版本号的 `.tar.gz`。

## 当前限制

- 桌面包应在目标平台本机上构建。当前没有使用 PyInstaller 做跨平台交叉编译。
- 现在的形态仍然是会自动打开浏览器的 desktop-style local bundle。macOS 产物还没有做代码签名或 notarization，Windows 侧目前也不产出 MSI。
- Windows 当前只明确支持 `x64`，因为 OpenCode vendoring 逻辑只支持 `windows-x64`。
- 源码构建默认要求 `masterbrain` 同级存在 `airalogy/` 和 `aimd/` 仓库。
- `.aira` 文件关联元数据已经写入 macOS app bundle 和 Windows 安装器脚本，但系统级真正注册仍取决于用户如何安装或启动这些产物。

## 构建入口

推荐使用跨平台命令：

```shell
cd apps/api
uv run masterbrain-build-desktop
```

平台封装脚本：

- macOS / Linux：`./scripts/build_desktop_bundle.sh`
- Windows PowerShell：`.\scripts\build_desktop_bundle.ps1`
