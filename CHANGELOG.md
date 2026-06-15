# Changelog

[中文版](CHANGELOG.zh-CN.md)

## Unreleased

- No changes yet.

## v0.9.0

### Added

- Added OpenCode-backed `endpoints/code_edit` support, allowing Airalogy Protocol Editor to understand and modify the current `protocol.aimd`, `model.py`, `assigner.py`, and `protocol.toml` through conversation.
- `code_edit` now supports `workspace_id`, so an editing session can reuse its OpenCode server process while each request still creates a fresh OpenCode session and treats the complete browser-provided file snapshot as the source of truth.

### Security and Stability

- Limited `code_edit` file changes to the four core Protocol Editor files and ignored out-of-scope edits such as helper files.
- Added syntax validation for returned AIMD, Python, and TOML changes, with risks surfaced to callers as warnings.
- Added a session-scoped OpenCode runtime manager with idle-timeout cleanup, a global runtime cap, a per-user namespace cap, same-workspace serialization, and service-shutdown cleanup.
- Tightened the `code_edit` execution log so it no longer exposes server temporary directories, the OpenCode binary path, or localhost ports to the frontend.

## v0.8.0

### Architecture

- Moved the Python distribution package from `apps/api` to `packages/masterbrain`, making the package and application boundaries clearer.
- Renamed the Vue frontend app from `apps/web` to `apps/studio`, aligning the app name with Masterbrain Studio as an independent frontend.
- Added `masterbrain.core` and `masterbrain.providers`, establishing clearer boundaries between the stateless AI core, model-provider adapters, and API endpoints.
- Updated the model invocation layer to use LiteLLM as the default provider-compatible adapter while preserving Masterbrain's own core/workflow boundaries, and excluded known affected LiteLLM versions `1.82.7` and `1.82.8` from dependency constraints.
- Added `openai`, `qwen`, `all-providers`, and `api` optional dependency extras to prepare for lighter core installation options.

### Changed

- Added the recommended `masterbrain-studio` startup entry point. The old `masterbrain-desktop` entry point remains as a deprecated compatibility alias and will be removed in a future version.
- Added a Python package release flow for `masterbrain` based on GitHub Actions and PyPI Trusted Publishing. Pushing a `v*` tag now validates the version, runs release tests, builds distributions, and publishes to PyPI.

### Added

- `packages/masterbrain` now depends directly on the released `airalogy` package and reuses `.aira` archive validation and unpacking logic.
- Added a local archive library that can import `.aira` files into SQLite and persist protocol metadata, record metadata, and record JSON locally.
- The desktop launcher now supports passing a `.aira` file path directly as the startup document.
- Added a `Library` view to the left sidebar in the web UI, allowing users to import `.aira` files, browse protocols and records, and reload library protocols into the current workspace.
- `apps/studio` now depends directly on the published npm packages `@airalogy/aimd-editor`, `@airalogy/aimd-renderer`, and `@airalogy/aimd-recorder`, integrating AIMD Monaco syntax and the AIMD renderer while replacing the previously maintained lightweight local `.aimd` parser/preview implementation.
- Added the cross-platform desktop packaging CLI `masterbrain-build-desktop`, which can also generate macOS `.app` bundles, Windows portable packages and installer scripts, Linux portable archives, plus macOS / Windows / Linux platform support matrix documentation.

## v0.7.0

### Added

- `endpoints/chat/qa/language` now supports: 1. thinking mode; 2. web search.
  The endpoint input structure is:

  ```json
  {
      "model": {
          "name": "qwen3.5-flash", // Can be qwen3.5-flash or qwen3.5-plus
          "enable_thinking": true, // Can be true or false
          "enable_search": true // Can be true or false
      },
      "messages": [
          {
              "role": "user",
              "content": "Think about who you are."
          }
      ]
  }
  ```

  The response is returned as a streaming string.

  A complete streaming response can look like:

  ```text
  <think>
  Thinking content...
  </think>
  I am Airalogy Masterbrain.
  ```

  Note that when `enable_thinking` is `true`, the thinking process is returned and wrapped in `<think>` tags. When it is `false`, only the final answer is returned and no `<think>` tags are included.

  @荣璐 The frontend should automatically render this tag separately from the final answer text.

### TODO

- `endpoints/chat/qa/vision`
- `endpoints/stt`

These endpoints still need to be refactored. @攀忠

## v0.6.0

- Completed the AIRA feature and its API.

## v0.2.1

- Removed the `chat_env` field from `ChatDoc` to reduce nesting complexity. See [`masterbrain.models.chat.ChatDoc`](/masterbrain/models/chat.py).

## v0.2.0

- Updated the `chat` endpoint to support the latest `ChatDoc` as the input data model. See [`masterbrain.models.chat.ChatDoc`](/masterbrain/models/chat.py).
- Added support for the latest `gpt-4o-mini` model.

## v0.1.0

- The `chat` endpoint supports the Tongyi Qianwen model `qwen-long`.
  After starting FastAPI, you can test it with [chat_doc_qwen.jsonc](test/test_fastapi/test_router/test_chat/chat_doc_qwen.jsonc) at <http://127.0.0.1:8000/docs#/default/post_chat_api_chat_post>. Remove comments from the jsonc file before testing so it becomes valid JSON.
- Adjusted the returned `assistant` value when calling tools by changing the `content` field from `null` to `""`. The main reason is that OpenAI models can run normally when the value is `null`, while Qwen models fail. When changed to `""`, both OpenAI and Qwen models work normally. Therefore, this change was made for compatibility. The underlying issue is that Qwen models are less tolerant of `null`; this is only a compatibility adjustment.

    ```json
    {
        "role": "assistant",
        "content": null,
        "tool_calls": [
            ...
        ]
    }
    ```

    ```json
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            ...
        ]
    }
    ```

- TODO: Qwen only supports alternating Assistant-User conversation patterns, as do some other commercial models such as ERNIE Bot. It does not support Assistant-Assistant-User conversation patterns. The current injection of `scenario_messages` can produce an Assistant-Assistant-User pattern, so the injection logic still needs to be adjusted.
