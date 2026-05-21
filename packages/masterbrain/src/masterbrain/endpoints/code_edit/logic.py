__all__ = [
    "OpenCodeRuntime",
    "build_code_edit_prompt",
    "compute_workspace_changes",
    "generate_code_edit_result",
]

import asyncio
import json
import logging
import os
import socket
import tempfile
from contextlib import asynccontextmanager, closing, suppress
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path, PurePosixPath

import httpx

from masterbrain.configs import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
)
from masterbrain.endpoints.code_edit.types import (
    CodeEditChangedFile,
    CodeEditInput,
    CodeEditOutput,
)
from masterbrain.utils.llm import ensure_model_api_key
from masterbrain.utils.opencode import missing_opencode_message, resolve_opencode_binary

SYSTEM_PROMPT = """You are editing an Airalogy Protocol workspace in a real project directory.

Use the workspace files on disk as the source of truth.

Rules:
- If the user asks for code changes, edit the files directly in the workspace.
- If the user asks a question, answer directly and avoid changing files unless necessary.
- Keep changes minimal and focused on the user's request.
- Prefer modifying existing files over creating new ones.
- Do not create or edit hidden files, runtime metadata, or config files unrelated to the request.
- Do not touch files outside the workspace.
- End with a short plain-language summary of what you changed or why no file changes were needed.
"""

SUPPORTED_EDIT_SUFFIXES = {
    ".aimd": "aimd",
    ".py": "py",
}
IGNORED_TOP_LEVEL_NAMES = {"opencode.json", "AGENTS.md"}
OPENCODE_LOG_TAIL_LIMIT = 40

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderConfig:
    provider_id: str
    model_id: str
    config: dict


@dataclass(frozen=True)
class OpenCodeRunResult:
    message: str
    execution_log: list[str]


@dataclass
class ProcessLogBuffer:
    stdout_tail: list[str]
    stderr_tail: list[str]
    tasks: list[asyncio.Task[None]]

    def __init__(self) -> None:
        self.stdout_tail = []
        self.stderr_tail = []
        self.tasks = []

    def start(self, process: asyncio.subprocess.Process) -> None:
        if process.stdout is not None:
            self.tasks.append(
                asyncio.create_task(
                    _drain_process_stream(process.stdout, "stdout", self.stdout_tail)
                )
            )
        if process.stderr is not None:
            self.tasks.append(
                asyncio.create_task(
                    _drain_process_stream(process.stderr, "stderr", self.stderr_tail)
                )
            )

    async def wait(self) -> None:
        if not self.tasks:
            return
        await asyncio.gather(*self.tasks, return_exceptions=True)


def _trim_for_log(text: str, limit: int = 240) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3]}..."


def _record_execution(
    execution_log: list[str],
    message: str,
    *,
    level: int = logging.INFO,
) -> None:
    execution_log.append(message)
    logger.log(level, "[code_edit] %s", message)


def _append_tail(buffer: list[str], text: str) -> None:
    buffer.append(text)
    if len(buffer) > OPENCODE_LOG_TAIL_LIMIT:
        del buffer[:-OPENCODE_LOG_TAIL_LIMIT]


def _format_process_tail(label: str, lines: list[str]) -> str:
    if not lines:
        return ""
    return f"{label} tail:\n" + "\n".join(lines)


async def _drain_process_stream(
    stream: asyncio.StreamReader,
    label: str,
    buffer: list[str],
) -> None:
    while True:
        line = await stream.readline()
        if not line:
            return
        text = line.decode("utf-8", errors="replace").rstrip()
        if not text:
            continue
        _append_tail(buffer, text)
        logger.info("[opencode %s] %s", label, text)


def _find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _is_hidden_or_internal(rel_path: str) -> bool:
    pure = PurePosixPath(rel_path)
    if pure.name in IGNORED_TOP_LEVEL_NAMES:
        return True
    return any(part.startswith(".") for part in pure.parts)


def _detect_supported_type(rel_path: str) -> str | None:
    return SUPPORTED_EDIT_SUFFIXES.get(PurePosixPath(rel_path).suffix)


def _safe_workspace_path(root: Path, rel_path: str) -> Path:
    pure = PurePosixPath(rel_path)
    if pure.is_absolute():
        raise ValueError(f"Absolute paths are not allowed: {rel_path}")
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"Unsafe relative path: {rel_path}")

    candidate = (root / pure.as_posix()).resolve()
    root_resolved = root.resolve()
    if root_resolved not in candidate.parents and candidate != root_resolved:
        raise ValueError(f"Path escapes workspace root: {rel_path}")
    return candidate


def _build_provider_config(
    model_name: str,
    *,
    require_api_key: bool = True,
) -> ProviderConfig:
    if model_name.startswith("qwen"):
        if require_api_key and not DASHSCOPE_API_KEY:
            raise RuntimeError(
                "DASHSCOPE_API_KEY is required for OpenCode-backed Qwen editing."
            )
        return ProviderConfig(
            provider_id="dashscope",
            model_id=model_name,
            config={
                "$schema": "https://opencode.ai/config.json",
                "permission": {
                    "edit": "allow",
                    "bash": "allow",
                },
                "provider": {
                    "dashscope": {
                        "npm": "@ai-sdk/openai-compatible",
                        "name": "DashScope",
                        "options": {
                            "baseURL": DASHSCOPE_BASE_URL
                            or "https://dashscope.aliyuncs.com/compatible-mode/v1",
                            "apiKey": "{env:DASHSCOPE_API_KEY}",
                        },
                        "models": {
                            "qwen3.5-flash": {
                                "name": "Qwen 3.5 Flash",
                                "limit": {"context": 131072, "output": 8192},
                            },
                            "qwen3.5-plus": {
                                "name": "Qwen 3.5 Plus",
                                "limit": {"context": 131072, "output": 8192},
                            },
                            "qwen3-max": {
                                "name": "Qwen 3 Max",
                                "limit": {"context": 32768, "output": 8192},
                            },
                        },
                    }
                },
            },
        )

    if model_name.startswith("gpt-"):
        if require_api_key and not OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is required for OpenCode-backed GPT editing."
            )
        return ProviderConfig(
            provider_id="openai",
            model_id=model_name,
            config={
                "$schema": "https://opencode.ai/config.json",
                "permission": {
                    "edit": "allow",
                    "bash": "allow",
                },
                "provider": {
                    "openai": {
                        "npm": "@ai-sdk/openai-compatible",
                        "name": "OpenAI",
                        "options": {
                            "baseURL": OPENAI_BASE_URL or "https://api.openai.com/v1",
                            "apiKey": "{env:OPENAI_API_KEY}",
                        },
                        "models": {
                            "gpt-4.1": {
                                "name": "GPT-4.1",
                                "limit": {"context": 1047576, "output": 32768},
                            },
                            "gpt-4.1-mini": {
                                "name": "GPT-4.1 Mini",
                                "limit": {"context": 1047576, "output": 32768},
                            },
                            "gpt-4o": {
                                "name": "GPT-4o",
                                "limit": {"context": 128000, "output": 16384},
                            },
                            "gpt-4o-mini": {
                                "name": "GPT-4o Mini",
                                "limit": {"context": 128000, "output": 16384},
                            },
                        },
                    }
                },
            },
        )

    raise RuntimeError(f"Unsupported code edit model: {model_name}")


def build_code_edit_prompt(code_edit_input: CodeEditInput) -> str:
    workspace_paths = sorted(file.path for file in code_edit_input.files)
    prompt_lines = [
        "You are working inside a temporary workspace that mirrors the current browser editor state.",
        "Use the workspace files on disk instead of asking the user to paste code again.",
        "",
        "Editor context:",
        f"- Active file: {code_edit_input.active_file_path or 'none'}",
        f"- Workspace file count: {len(workspace_paths)}",
    ]

    if workspace_paths:
        prompt_lines.append("- Workspace files:")
        prompt_lines.extend(f"  - {path}" for path in workspace_paths)

    if code_edit_input.selection:
        prompt_lines.extend(
            [
                "",
                "Current selection in the active file:",
                f"- Start offset: {code_edit_input.selection.start_offset}",
                f"- End offset: {code_edit_input.selection.end_offset}",
                "```",
                code_edit_input.selection.text,
                "```",
            ]
        )

    if code_edit_input.chat_history:
        prompt_lines.extend(["", "Recent conversation:"])
        for message in code_edit_input.chat_history[-12:]:
            role = "User" if message.role == "user" else "Assistant"
            prompt_lines.append(f"{role}: {message.content}")

    prompt_lines.extend(["", "Current user request:", code_edit_input.prompt])

    return "\n".join(prompt_lines).strip()


def _materialize_workspace(root: Path, code_edit_input: CodeEditInput) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for workspace_file in code_edit_input.files:
        path = _safe_workspace_path(root, workspace_file.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(workspace_file.content, encoding="utf-8")
        snapshot[workspace_file.path] = workspace_file.content
    return snapshot


def _collect_workspace_state(root: Path) -> dict[str, str]:
    state: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root).as_posix()
        if _is_hidden_or_internal(rel_path):
            continue
        state[rel_path] = path.read_text(encoding="utf-8", errors="ignore")
    return state


def compute_workspace_changes(
    before_state: dict[str, str],
    after_state: dict[str, str],
) -> tuple[list[CodeEditChangedFile], list[str]]:
    changed_files: list[CodeEditChangedFile] = []
    warnings: list[str] = []

    all_paths = sorted(set(before_state) | set(after_state))
    for rel_path in all_paths:
        before = before_state.get(rel_path)
        after = after_state.get(rel_path)
        supported_type = _detect_supported_type(rel_path)

        if before == after:
            continue

        if supported_type is None:
            warnings.append(
                f"Ignored unsupported file change outside the current UI scope: {rel_path}"
            )
            continue

        if before is None and after is not None:
            status = "created"
            diff = "\n".join(
                unified_diff(
                    [],
                    after.splitlines(),
                    fromfile=f"a/{rel_path}",
                    tofile=f"b/{rel_path}",
                    lineterm="",
                )
            )
            content = after
        elif before is not None and after is None:
            status = "deleted"
            diff = "\n".join(
                unified_diff(
                    before.splitlines(),
                    [],
                    fromfile=f"a/{rel_path}",
                    tofile=f"b/{rel_path}",
                    lineterm="",
                )
            )
            content = ""
        else:
            status = "modified"
            diff = "\n".join(
                unified_diff(
                    before.splitlines(),
                    after.splitlines(),
                    fromfile=f"a/{rel_path}",
                    tofile=f"b/{rel_path}",
                    lineterm="",
                )
            )
            content = after or ""

        changed_files.append(
            CodeEditChangedFile(
                path=rel_path,
                name=PurePosixPath(rel_path).name,
                type=supported_type,  # type: ignore[arg-type]
                status=status,  # type: ignore[arg-type]
                content=content,
                diff=diff,
            )
        )

    return changed_files, warnings


async def _wait_for_server(
    port: int,
    process: asyncio.subprocess.Process,
    process_logs: ProcessLogBuffer,
) -> None:
    base_url = f"http://127.0.0.1:{port}"
    timeout_at = asyncio.get_running_loop().time() + 20
    async with httpx.AsyncClient(timeout=httpx.Timeout(2.0, connect=2.0)) as client:
        while True:
            if process.returncode is not None:
                stderr_tail = _format_process_tail("stderr", process_logs.stderr_tail)
                stdout_tail = _format_process_tail("stdout", process_logs.stdout_tail)
                extra_parts = [part for part in (stderr_tail, stdout_tail) if part]
                extra = f"\n\n{'\n\n'.join(extra_parts)}" if extra_parts else ""
                raise RuntimeError(
                    "opencode server exited during startup."
                    f"{extra}"
                )

            try:
                response = await client.get(f"{base_url}/global/health")
                if response.is_success:
                    return
            except httpx.HTTPError:
                pass

            if asyncio.get_running_loop().time() >= timeout_at:
                raise RuntimeError("Timed out while waiting for opencode server startup.")

            await asyncio.sleep(0.25)


async def _terminate_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    with suppress(ProcessLookupError):
        process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=5)
    except asyncio.TimeoutError:
        with suppress(ProcessLookupError):
            process.kill()
        await process.wait()


@asynccontextmanager
async def _opencode_server(workspace_dir: Path, config: dict):
    opencode_binary = resolve_opencode_binary()
    if not opencode_binary:
        raise RuntimeError(missing_opencode_message())

    port = _find_free_port()
    env = os.environ.copy()
    env["OPENCODE_CONFIG_CONTENT"] = json.dumps(config)

    process = await asyncio.create_subprocess_exec(
        str(opencode_binary),
        "serve",
        "--hostname",
        "127.0.0.1",
        "--port",
        str(port),
        cwd=str(workspace_dir),
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    process_logs = ProcessLogBuffer()
    process_logs.start(process)

    try:
        await _wait_for_server(port, process, process_logs)
        yield f"http://127.0.0.1:{port}", opencode_binary
    finally:
        await _terminate_process(process)
        await process_logs.wait()


class OpenCodeRuntime:
    """Thin wrapper around a short-lived opencode server process."""

    async def run(
        self,
        workspace_dir: Path,
        *,
        system_prompt: str,
        user_prompt: str,
        provider_id: str,
        model_id: str,
        config: dict,
    ) -> OpenCodeRunResult:
        execution_log: list[str] = []
        async with _opencode_server(workspace_dir, config) as (
            base_url,
            opencode_binary,
        ):
            _record_execution(
                execution_log,
                f"OpenCode runtime: {opencode_binary}",
            )
            _record_execution(
                execution_log,
                f"OpenCode server is ready at {base_url}",
            )
            timeout = httpx.Timeout(300.0, connect=10.0, read=300.0, write=60.0)
            async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
                session_response = await client.post(
                    "/session",
                    json={"title": "Masterbrain Code Edit"},
                )
                session_response.raise_for_status()
                session_id = session_response.json()["id"]
                _record_execution(
                    execution_log,
                    f"Created OpenCode session {session_id}.",
                )

                chat_response = await client.post(
                    f"/session/{session_id}/message",
                    json={
                        "providerID": provider_id,
                        "modelID": model_id,
                        "system": system_prompt,
                        "parts": [{"type": "text", "text": user_prompt}],
                    },
                )
                chat_response.raise_for_status()
                assistant_message = chat_response.json()
                if assistant_message.get("error"):
                    raise RuntimeError(
                        f"OpenCode returned an error: {assistant_message['error']}"
                    )
                _record_execution(
                    execution_log,
                    f"Submitted edit request to {provider_id}/{model_id}.",
                )

                messages_response = await client.get(f"/session/{session_id}/message")
                messages_response.raise_for_status()
                messages = messages_response.json()
                _record_execution(
                    execution_log,
                    f"Fetched {len(messages)} message(s) from OpenCode session history.",
                )

        summary = "OpenCode completed without returning a text summary."
        for message in reversed(messages):
            info = message.get("info", {})
            if info.get("role") != "assistant":
                continue
            text_parts = [
                part.get("text", "").strip()
                for part in message.get("parts", [])
                if part.get("type") == "text" and part.get("text")
            ]
            if text_parts:
                summary = "\n\n".join(text_parts)
                break

        _record_execution(
            execution_log,
            f"Assistant summary: {_trim_for_log(summary)}",
        )
        return OpenCodeRunResult(message=summary, execution_log=execution_log)


async def generate_code_edit_result(
    code_edit_input: CodeEditInput,
    runtime: OpenCodeRuntime | None = None,
) -> CodeEditOutput:
    validate_api_key = runtime is None
    runtime = runtime or OpenCodeRuntime()
    warnings: list[str] = []
    execution_log: list[str] = []

    if validate_api_key:
        ensure_model_api_key(code_edit_input.model.name)
    _record_execution(
        execution_log,
        f"Starting code edit request with model {code_edit_input.model.name}.",
    )
    _record_execution(
        execution_log,
        "Workspace snapshot: "
        f"{len(code_edit_input.files)} file(s), "
        f"active file {code_edit_input.active_file_path or 'none'}.",
    )

    if code_edit_input.model.enable_thinking:
        warnings.append(
            "The current OpenCode integration does not forward the frontend `enable_thinking` flag."
        )

    provider = _build_provider_config(
        code_edit_input.model.name,
        require_api_key=validate_api_key,
    )
    user_prompt = build_code_edit_prompt(code_edit_input)
    _record_execution(
        execution_log,
        f"Selected provider {provider.provider_id}/{provider.model_id}.",
    )

    with tempfile.TemporaryDirectory(prefix="masterbrain-opencode-") as tmp_dir:
        workspace_dir = Path(tmp_dir)
        before_state = _materialize_workspace(workspace_dir, code_edit_input)
        _record_execution(
            execution_log,
            f"Materialized {len(before_state)} workspace file(s) in {workspace_dir}.",
        )

        run_result = await runtime.run(
            workspace_dir,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            provider_id=provider.provider_id,
            model_id=provider.model_id,
            config=provider.config,
        )
        execution_log.extend(run_result.execution_log)

        after_state = _collect_workspace_state(workspace_dir)
        _record_execution(
            execution_log,
            f"Collected {len(after_state)} file(s) from the updated workspace snapshot.",
        )

    changed_files, change_warnings = compute_workspace_changes(before_state, after_state)
    warnings.extend(change_warnings)
    if changed_files:
        changed_labels = ", ".join(
            f"{change.path} ({change.status})" for change in changed_files
        )
        _record_execution(
            execution_log,
            f"Detected {len(changed_files)} supported file change(s): {changed_labels}.",
        )
    else:
        _record_execution(
            execution_log,
            "OpenCode finished successfully but no supported workspace files changed.",
            level=logging.WARNING,
        )
    if warnings:
        _record_execution(
            execution_log,
            f"Warnings: {'; '.join(warnings)}",
            level=logging.WARNING,
        )

    return CodeEditOutput(
        message=run_result.message,
        edit_status="changed" if changed_files else "no_changes",
        changed_files=changed_files,
        warnings=warnings,
        execution_log=execution_log,
    )
