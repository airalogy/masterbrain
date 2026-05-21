# Workspace and Editing

## Directory-first model

Masterbrain no longer treats the workspace as an abstract in-memory project. The primary model is a real directory on disk.

You can:

- launch directly against a directory with `masterbrain-studio --workspace /path/to/project`
- choose a directory from the sidebar
- paste a path into the UI
- import a ZIP archive into the selected directory
- export the current directory back to ZIP

Edits made from the UI are written directly to disk.

## Workspace API surface

The backend exposes a dedicated workspace router under `/api/endpoints`:

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

These routes return a `WorkspaceState` snapshot that includes the root path, files, folders, and whether directory selection is supported on the current platform.

## Code editing

Code editing is handled by `POST /api/endpoints/code_edit`.

The request includes:

- the active prompt
- the materialized workspace files
- the currently focused file
- the current editor selection
- compact chat history
- the chosen model configuration

The response reports:

- whether anything changed
- changed files and their latest content
- unified diffs
- runtime warnings
- execution logs

In source and development mode, the backend shells out to a local `opencode` binary. In the packaged desktop bundle, OpenCode is bundled automatically.

## Why this split matters

The workspace router owns deterministic file operations. The code-edit router owns AI-driven edits. Keeping them separate makes it easier to reason about permissions, error handling, and what part of the system is responsible for each change.
