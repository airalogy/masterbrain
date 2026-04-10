"""Desktop-style launcher for Masterbrain.

This starts the FastAPI backend, serves the built web frontend from the same
process, and opens the UI in the user's default browser. The packaged app is
expected to include a bundled OpenCode CLI for chat-driven code editing.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn

from masterbrain.library_store import library_store
from masterbrain.utils.opencode import missing_opencode_message, resolve_opencode_binary


def _find_free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _wait_for_server(host: str, port: int, timeout_s: float = 15.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.15)
    raise RuntimeError(f"Timed out waiting for Masterbrain at http://{host}:{port}")


def _print_opencode_status() -> None:
    opencode_binary = resolve_opencode_binary()
    if opencode_binary is None:
        print(f"Warning: {missing_opencode_message()}", file=sys.stderr)
        return

    print(f"Using OpenCode runtime: {opencode_binary}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Launch Masterbrain as a single local desktop-style app."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument(
        "document",
        nargs="?",
        help="Optional workspace directory or .aira archive path to open on launch.",
    )
    parser.add_argument(
        "--workspace",
        help="Open Masterbrain against an existing local workspace directory.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start the local app without opening a browser window automatically.",
    )
    args = parser.parse_args()

    workspace_path = args.workspace
    archive_path: str | None = None

    if args.document:
        document = Path(args.document).expanduser().resolve()
        if document.is_dir() and workspace_path is None:
            workspace_path = str(document)
        elif document.is_file() and document.suffix == ".aira":
            archive_path = str(document)
        elif not document.exists():
            raise RuntimeError(f"Document path does not exist: {document}")
        else:
            raise RuntimeError(
                "Desktop launcher accepts a workspace directory or a .aira archive path."
            )

    if workspace_path:
        os.environ["MASTERBRAIN_WORKSPACE_DIR"] = workspace_path

    if archive_path:
        result = library_store.import_archive_path(archive_path)
        import_result = result["result"]
        action = "Reused existing" if import_result["duplicate"] else "Imported"
        print(
            f"{action} {import_result['kind']} archive into local library: "
            f"{import_result['source_name']}"
        )

    from masterbrain.fastapi.main import WEB_DIST_DIR, app

    if WEB_DIST_DIR is None:
        raise RuntimeError(
            "Built web assets were not found. Run `npm run build` in `apps/web` first, "
            "or set `MASTERBRAIN_WEB_DIST` to a built frontend directory."
        )

    _print_opencode_status()
    if workspace_path:
        print(f"Using workspace directory: {workspace_path}")

    host = args.host
    port = args.port or _find_free_port()
    url = f"http://{host}:{port}"

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=False)
    thread.start()

    _wait_for_server(host, port)
    print(f"Masterbrain is running at {url}")

    if not args.no_browser:
        webbrowser.open(url)

    thread.join()


if __name__ == "__main__":
    main()
