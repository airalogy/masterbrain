__all__ = [
    "OpenCodeRuntime",
    "OpenCodeRuntimeManager",
    "build_code_edit_prompt",
    "compute_workspace_changes",
    "generate_code_edit_result",
    "shutdown_code_edit_runtime_manager",
]

import asyncio
import ast
import hashlib
import json
import logging
import os
import shutil
import socket
import tempfile
import tomllib
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
- Edit only the current Protocol editor files: protocol.aimd, model.py, assigner.py, and protocol.toml.
- Prefer modifying existing files over creating new ones. Do not create helper files.
- Keep protocol.aimd valid AIMD. Variables should be declared with `{{var|name: Type}}` when a type is known.
- Keep assigner logic compatible with Airalogy assigner syntax. In AIMD, assigner blocks are fenced with ```assigner ... ```. In standalone assigner.py, write the assigner code only, without Markdown fences.
- Use the current module-level, function-based assigner syntax: `from airalogy.assigner import AssignerResult, assigner`, decorate plain functions with `@assigner(assigned_fields=[...], dependent_fields=[...], mode="auto")`, take a single `dependent_fields: dict` argument, and return `AssignerResult(assigned_fields={...})`. Do not use the deprecated `AssignerBase`, `class Assigner`, `@staticmethod`, or a `dependent_data` parameter. For Variable Table fields, reference them as `"table_name.subvar_name"`.
- Keep model.py valid Python and aligned with fields referenced by protocol.aimd and assigner.py.
- Keep protocol.toml valid TOML.
- Do not create or edit hidden files, runtime metadata, or config files unrelated to the request.
- Do not touch files outside the workspace.
- End with a short plain-language summary of what you changed or why no file changes were needed.
"""

SUPPORTED_EDIT_SUFFIXES = {
    ".aimd": "aimd",
    ".py": "py",
    ".toml": "toml",
}
ALLOWED_EDIT_PATHS = {"protocol.aimd", "model.py", "assigner.py", "protocol.toml"}
IGNORED_TOP_LEVEL_NAMES = {"opencode.json", "AGENTS.md"}
OPENCODE_LOG_TAIL_LIMIT = 40
CODE_EDIT_IDLE_TIMEOUT_SECONDS = int(
    os.getenv("MASTERBRAIN_CODE_EDIT_IDLE_TIMEOUT_SECONDS", "900")
)
CODE_EDIT_MAX_MANAGED_RUNTIMES = int(
    os.getenv("MASTERBRAIN_CODE_EDIT_MAX_MANAGED_RUNTIMES", "16")
)
CODE_EDIT_MAX_MANAGED_RUNTIMES_PER_NAMESPACE = int(
    os.getenv("MASTERBRAIN_CODE_EDIT_MAX_MANAGED_RUNTIMES_PER_NAMESPACE", "2")
)

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


@dataclass(frozen=True)
class OpenCodeServerProcess:
    base_url: str
    opencode_binary: Path
    process: asyncio.subprocess.Process
    process_logs: "ProcessLogBuffer"


@dataclass
class ManagedOpenCodeRuntimeEntry:
    workspace_id: str
    workspace_dir: Path
    config_key: str
    server: OpenCodeServerProcess
    lock: asyncio.Lock
    last_used_at: float
    active_requests: int = 0


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
    pure = PurePosixPath(rel_path)
    if pure.as_posix() not in ALLOWED_EDIT_PATHS:
        return None
    return SUPPORTED_EDIT_SUFFIXES.get(pure.suffix)


def _trim_warning(text: str, limit: int = 800) -> str:
    normalized = " ".join(str(text).split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3]}..."


def _validate_aimd_content(content: str) -> tuple[bool, object, str | None]:
    try:
        from airalogy.markdown import validate_aimd
    except ModuleNotFoundError:
        return (
            True,
            [],
            "AIMD syntax validation skipped because the `airalogy` package is not installed.",
        )

    is_valid, errors = validate_aimd(content)
    return is_valid, errors, None


def validate_changed_file(change: CodeEditChangedFile) -> list[str]:
    if change.status == "deleted":
        return [f"{change.path} was deleted. Review carefully before applying."]

    if change.type == "aimd":
        is_valid, errors, skipped_warning = _validate_aimd_content(change.content)
        if skipped_warning:
            return [skipped_warning]
        if not is_valid:
            return [f"{change.path} has invalid AIMD syntax: {_trim_warning(str(errors))}"]
        return []

    if change.type == "py":
        try:
            ast.parse(change.content)
        except SyntaxError as exc:
            location = f"line {exc.lineno}"
            if exc.offset:
                location = f"{location}, column {exc.offset}"
            return [f"{change.path} has invalid Python syntax at {location}: {exc.msg}"]
        return []

    if change.type == "toml":
        try:
            tomllib.loads(change.content)
        except tomllib.TOMLDecodeError as exc:
            return [f"{change.path} has invalid TOML syntax: {_trim_warning(str(exc))}"]
        return []

    return []


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


def _sync_workspace(root: Path, code_edit_input: CodeEditInput) -> dict[str, str]:
    incoming_paths = {PurePosixPath(file.path).as_posix() for file in code_edit_input.files}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root).as_posix()
        if _is_hidden_or_internal(rel_path):
            continue
        if rel_path not in incoming_paths:
            path.unlink()

    return _materialize_workspace(root, code_edit_input)


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
                f"Ignored unsupported file change outside the current Protocol editor scope: {rel_path}"
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


async def _start_opencode_server(
    workspace_dir: Path,
    config: dict,
) -> OpenCodeServerProcess:
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

    await _wait_for_server(port, process, process_logs)
    return OpenCodeServerProcess(
        base_url=f"http://127.0.0.1:{port}",
        opencode_binary=opencode_binary,
        process=process,
        process_logs=process_logs,
    )


async def _stop_opencode_server(server: OpenCodeServerProcess) -> None:
    await _terminate_process(server.process)
    await server.process_logs.wait()


@asynccontextmanager
async def _opencode_server(workspace_dir: Path, config: dict):
    server = await _start_opencode_server(workspace_dir, config)
    try:
        yield server.base_url, server.opencode_binary
    finally:
        await _stop_opencode_server(server)


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
                "OpenCode runtime is available.",
            )
            _record_execution(
                execution_log,
                "OpenCode server is ready.",
            )
            return await _run_opencode_message(
                base_url,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                provider_id=provider_id,
                model_id=model_id,
                execution_log=execution_log,
            )


async def _run_opencode_message(
    base_url: str,
    *,
    system_prompt: str,
    user_prompt: str,
    provider_id: str,
    model_id: str,
    execution_log: list[str],
) -> OpenCodeRunResult:
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
            raise RuntimeError(f"OpenCode returned an error: {assistant_message['error']}")
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


def _opencode_config_key(config: dict) -> str:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _workspace_label(workspace_id: str) -> str:
    return hashlib.sha256(workspace_id.encode("utf-8")).hexdigest()[:16]


def _workspace_namespace(workspace_id: str) -> str:
    parts = workspace_id.split(":", 3)
    if len(parts) >= 2 and parts[0] == "user" and parts[1]:
        return f"user:{parts[1]}"
    return f"workspace:{_workspace_label(workspace_id)}"


class OpenCodeRuntimeManager:
    """Session-scoped OpenCode server manager.

    The manager reuses the OpenCode server process per workspace_id, but each
    request still creates a fresh OpenCode session. Browser-supplied files are
    synchronized into the workspace before every request.
    """

    def __init__(
        self,
        *,
        idle_timeout_seconds: int = CODE_EDIT_IDLE_TIMEOUT_SECONDS,
        max_runtimes: int = CODE_EDIT_MAX_MANAGED_RUNTIMES,
    ) -> None:
        self.idle_timeout_seconds = idle_timeout_seconds
        self.max_runtimes = max_runtimes
        self._entries: dict[str, ManagedOpenCodeRuntimeEntry] = {}
        self._lock = asyncio.Lock()

    async def run(
        self,
        workspace_id: str,
        code_edit_input: CodeEditInput,
        *,
        system_prompt: str,
        user_prompt: str,
        provider_id: str,
        model_id: str,
        config: dict,
    ) -> tuple[OpenCodeRunResult, dict[str, str], dict[str, str], list[str]]:
        execution_log: list[str] = []
        entry = await self._get_or_create_entry(workspace_id, config, execution_log)

        try:
            async with entry.lock:
                entry.last_used_at = asyncio.get_running_loop().time()
                before_state = _sync_workspace(entry.workspace_dir, code_edit_input)
                _record_execution(
                    execution_log,
                    f"Synchronized {len(before_state)} workspace file(s) in managed workspace.",
                )

                run_result = await _run_opencode_message(
                    entry.server.base_url,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    provider_id=provider_id,
                    model_id=model_id,
                    execution_log=execution_log,
                )

                after_state = _collect_workspace_state(entry.workspace_dir)
                entry.last_used_at = asyncio.get_running_loop().time()
                _record_execution(
                    execution_log,
                    f"Collected {len(after_state)} file(s) from managed workspace snapshot.",
                )
        finally:
            await self._release_entry(entry)

        return run_result, before_state, after_state, execution_log

    async def shutdown(self) -> None:
        async with self._lock:
            entries = list(self._entries.values())
            self._entries.clear()

        for entry in entries:
            await self._shutdown_entry(entry)

    async def _get_or_create_entry(
        self,
        workspace_id: str,
        config: dict,
        execution_log: list[str],
    ) -> ManagedOpenCodeRuntimeEntry:
        config_key = _opencode_config_key(config)
        label = _workspace_label(workspace_id)

        async with self._lock:
            await self._cleanup_idle_locked(execution_log)

            existing = self._entries.get(workspace_id)
            if (
                existing
                and existing.config_key == config_key
                and existing.server.process.returncode is None
            ):
                existing.active_requests += 1
                _record_execution(
                    execution_log,
                    f"Reusing managed OpenCode runtime {label}.",
                )
                return existing

            if existing:
                if existing.lock.locked() or existing.active_requests > 0:
                    raise RuntimeError(
                        "OpenCode runtime is busy and cannot be restarted for a model/configuration change. Please retry after the current edit finishes."
                    )
                await self._shutdown_entry(existing)
                self._entries.pop(workspace_id, None)

            await self._evict_for_namespace_capacity_locked(workspace_id, execution_log)
            namespace_count = self._count_namespace_locked(workspace_id)
            if namespace_count >= CODE_EDIT_MAX_MANAGED_RUNTIMES_PER_NAMESPACE:
                raise RuntimeError(
                    "OpenCode runtime capacity reached for this user. Please retry after another editor session becomes idle."
                )

            await self._evict_for_capacity_locked(execution_log)
            if len(self._entries) >= self.max_runtimes:
                raise RuntimeError(
                    "OpenCode runtime capacity reached. Please retry after another editor session becomes idle."
                )

            workspace_dir = Path(
                tempfile.mkdtemp(prefix=f"masterbrain-opencode-{label}-")
            )
            try:
                server = await _start_opencode_server(workspace_dir, config)
            except Exception:
                shutil.rmtree(workspace_dir, ignore_errors=True)
                raise
            entry = ManagedOpenCodeRuntimeEntry(
                workspace_id=workspace_id,
                workspace_dir=workspace_dir,
                config_key=config_key,
                server=server,
                lock=asyncio.Lock(),
                last_used_at=asyncio.get_running_loop().time(),
                active_requests=1,
            )
            self._entries[workspace_id] = entry
            _record_execution(
                execution_log,
                f"Started managed OpenCode runtime {label}.",
            )
            return entry

    async def _cleanup_idle_locked(self, execution_log: list[str]) -> None:
        if self.idle_timeout_seconds <= 0:
            return

        now = asyncio.get_running_loop().time()
        idle_entries = [
            (workspace_id, entry)
            for workspace_id, entry in self._entries.items()
            if not entry.lock.locked()
            and entry.active_requests == 0
            and now - entry.last_used_at >= self.idle_timeout_seconds
        ]
        for workspace_id, entry in idle_entries:
            await self._shutdown_entry(entry)
            self._entries.pop(workspace_id, None)
            _record_execution(
                execution_log,
                f"Stopped idle managed OpenCode runtime {_workspace_label(workspace_id)}.",
            )

    async def _evict_for_capacity_locked(self, execution_log: list[str]) -> None:
        if len(self._entries) < self.max_runtimes:
            return

        evictable = [
            (workspace_id, entry)
            for workspace_id, entry in self._entries.items()
            if not entry.lock.locked() and entry.active_requests == 0
        ]
        if not evictable:
            return

        workspace_id, entry = min(evictable, key=lambda item: item[1].last_used_at)
        await self._shutdown_entry(entry)
        self._entries.pop(workspace_id, None)
        _record_execution(
            execution_log,
            f"Evicted least recently used managed OpenCode runtime {_workspace_label(workspace_id)}.",
        )

    async def _evict_for_namespace_capacity_locked(
        self,
        workspace_id: str,
        execution_log: list[str],
    ) -> None:
        if CODE_EDIT_MAX_MANAGED_RUNTIMES_PER_NAMESPACE <= 0:
            return
        if self._count_namespace_locked(workspace_id) < CODE_EDIT_MAX_MANAGED_RUNTIMES_PER_NAMESPACE:
            return

        namespace = _workspace_namespace(workspace_id)
        evictable = [
            (entry_workspace_id, entry)
            for entry_workspace_id, entry in self._entries.items()
            if _workspace_namespace(entry_workspace_id) == namespace
            and not entry.lock.locked()
            and entry.active_requests == 0
        ]
        if not evictable:
            return

        evicted_workspace_id, entry = min(evictable, key=lambda item: item[1].last_used_at)
        await self._shutdown_entry(entry)
        self._entries.pop(evicted_workspace_id, None)
        _record_execution(
            execution_log,
            f"Evicted least recently used managed OpenCode runtime for namespace {_workspace_label(namespace)}.",
        )

    def _count_namespace_locked(self, workspace_id: str) -> int:
        namespace = _workspace_namespace(workspace_id)
        return sum(
            1
            for entry_workspace_id in self._entries
            if _workspace_namespace(entry_workspace_id) == namespace
        )

    async def _release_entry(self, entry: ManagedOpenCodeRuntimeEntry) -> None:
        async with self._lock:
            entry.active_requests = max(entry.active_requests - 1, 0)
            entry.last_used_at = asyncio.get_running_loop().time()

    async def _shutdown_entry(self, entry: ManagedOpenCodeRuntimeEntry) -> None:
        await _stop_opencode_server(entry.server)
        shutil.rmtree(entry.workspace_dir, ignore_errors=True)


_CODE_EDIT_RUNTIME_MANAGER = OpenCodeRuntimeManager()


async def shutdown_code_edit_runtime_manager() -> None:
    await _CODE_EDIT_RUNTIME_MANAGER.shutdown()


async def generate_code_edit_result(
    code_edit_input: CodeEditInput,
    runtime: OpenCodeRuntime | None = None,
) -> CodeEditOutput:
    validate_api_key = runtime is None
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

    if runtime is None and code_edit_input.workspace_id:
        (
            run_result,
            before_state,
            after_state,
            managed_execution_log,
        ) = await _CODE_EDIT_RUNTIME_MANAGER.run(
            code_edit_input.workspace_id,
            code_edit_input,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            provider_id=provider.provider_id,
            model_id=provider.model_id,
            config=provider.config,
        )
        execution_log.extend(managed_execution_log)
    else:
        runtime = runtime or OpenCodeRuntime()
        with tempfile.TemporaryDirectory(prefix="masterbrain-opencode-") as tmp_dir:
            workspace_dir = Path(tmp_dir)
            before_state = _sync_workspace(workspace_dir, code_edit_input)
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
    for change in changed_files:
        warnings.extend(validate_changed_file(change))
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
