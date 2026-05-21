# 工作区与代码编辑

## 目录优先的工作模型

Masterbrain 现在不再把工作区看作抽象的内存工程，而是直接面向磁盘上的真实目录。

你可以：

- 用 `masterbrain-studio --workspace /path/to/project` 直接绑定一个目录启动
- 在侧边栏里选择目录
- 在 UI 中粘贴路径
- 把 ZIP 导入到当前目录
- 将当前目录导出为 ZIP

界面里的修改会直接写回磁盘。

## Workspace API

后端在 `/api/endpoints` 下提供独立的工作区路由：

- `GET /workspace`
- `POST /workspace/open`
- `POST /workspace/select`
- `PUT /workspace/file`
- `POST /workspace/file`
- `DELETE /workspace/file`
- `POST /workspace/rename`
- `POST /workspace/folder`
- `POST /workspace/import-zip`
- `GET /workspace/export-zip`

这些接口统一返回 `WorkspaceState` 快照，其中包含根目录路径、文件列表、文件夹列表，以及当前平台是否支持目录选择。

## 代码编辑

代码编辑由 `POST /api/endpoints/code_edit` 负责。

请求中主要包含：

- 当前用户提示词
- 已物化的工作区文件
- 当前激活文件
- 编辑器选区
- 精简后的聊天历史
- 所选模型配置

响应中会返回：

- 是否产生改动
- 被修改文件及其最新内容
- unified diff
- 运行时警告
- 执行日志

在源代码运行和开发模式下，后端会调用本地 `opencode` 二进制；在打包后的桌面版本中，OpenCode 会一并被打进应用包中。

## 为什么要分开

`workspace` 路由负责确定性的文件操作，`code_edit` 路由负责 AI 驱动的修改生成。这样拆分之后，权限边界、错误处理和责任归属都会更清晰。
