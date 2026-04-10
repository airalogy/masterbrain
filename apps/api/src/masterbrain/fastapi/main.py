"""
Main file for FastAPI server.
"""

import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    PermissionDeniedError,
    RateLimitError,
)

from masterbrain.endpoints import (
    chat_qa_language_router,
    chat_qa_stt_router,
    chat_qa_vision_router,
    code_edit_router,
    field_input_router,
    library_router,
    paper_generation_router,
    protocol_check_router,
    protocol_debug_router,
    protocol_generation_aimd_router,
    protocol_generation_assigner_router,
    protocol_generation_model_router,
    single_protocol_file_generation_router,
    workspace_router,
)
from masterbrain.endpoints.aira.router import aira_router
from masterbrain.utils.llm import llm_http_exception

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ENDPOINTS_PREFIX = "/api/endpoints"


def _json_error_response(status_code: int, detail: object) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


@app.exception_handler(AuthenticationError)
async def handle_authentication_error(_: Request, exc: AuthenticationError) -> JSONResponse:
    http_exc = llm_http_exception(exc)
    return _json_error_response(http_exc.status_code, http_exc.detail)


@app.exception_handler(PermissionDeniedError)
async def handle_permission_denied(_: Request, exc: PermissionDeniedError) -> JSONResponse:
    http_exc = llm_http_exception(exc)
    return _json_error_response(http_exc.status_code, http_exc.detail)


@app.exception_handler(RateLimitError)
async def handle_rate_limit(_: Request, exc: RateLimitError) -> JSONResponse:
    http_exc = llm_http_exception(exc)
    return _json_error_response(http_exc.status_code, http_exc.detail)


@app.exception_handler(APITimeoutError)
async def handle_api_timeout(_: Request, exc: APITimeoutError) -> JSONResponse:
    http_exc = llm_http_exception(exc)
    return _json_error_response(http_exc.status_code, http_exc.detail)


@app.exception_handler(APIConnectionError)
async def handle_api_connection(_: Request, exc: APIConnectionError) -> JSONResponse:
    http_exc = llm_http_exception(exc)
    return _json_error_response(http_exc.status_code, http_exc.detail)


@app.exception_handler(BadRequestError)
async def handle_bad_request(_: Request, exc: BadRequestError) -> JSONResponse:
    http_exc = llm_http_exception(exc)
    return _json_error_response(http_exc.status_code, http_exc.detail)


@app.exception_handler(APIStatusError)
async def handle_api_status(_: Request, exc: APIStatusError) -> JSONResponse:
    http_exc = llm_http_exception(exc)
    return _json_error_response(http_exc.status_code, http_exc.detail)


def _resolve_web_dist_dir() -> Path | None:
    override = os.getenv("MASTERBRAIN_WEB_DIST")
    if override:
        candidate = Path(override).expanduser().resolve()
        if candidate.exists():
            return candidate

    api_root = Path(__file__).resolve().parents[3]
    if api_root.name == "api" and api_root.parent.name == "apps":
        repo_candidate = api_root.parent / "web" / "dist"
        if repo_candidate.exists():
            return repo_candidate

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            frozen_root = Path(meipass)
            for candidate in (
                frozen_root / "web_dist",
                frozen_root / "src" / "web" / "dist",
                frozen_root / "web" / "dist",
            ):
                if candidate.exists():
                    return candidate

    return None


WEB_DIST_DIR = _resolve_web_dist_dir()


# AIRA #########################################################################
app.include_router(aira_router, prefix=ENDPOINTS_PREFIX, tags=["AIRA"])


# Chat #########################################################################
app.include_router(chat_qa_language_router, prefix=ENDPOINTS_PREFIX, tags=["Chat"])
app.include_router(chat_qa_vision_router, prefix=ENDPOINTS_PREFIX, tags=["Chat"])
app.include_router(chat_qa_stt_router, prefix=ENDPOINTS_PREFIX, tags=["Chat"])
app.include_router(field_input_router, prefix=ENDPOINTS_PREFIX, tags=["Chat"])
app.include_router(code_edit_router, prefix=ENDPOINTS_PREFIX, tags=["Chat"])
app.include_router(library_router, prefix=ENDPOINTS_PREFIX, tags=["Library"])
app.include_router(workspace_router, prefix=ENDPOINTS_PREFIX, tags=["Workspace"])


# Protocol Generation ##########################################################
app.include_router(
    protocol_generation_aimd_router,
    prefix=ENDPOINTS_PREFIX,
    tags=["Protocol Generation"],
)
app.include_router(
    protocol_generation_model_router,
    prefix=ENDPOINTS_PREFIX,
    tags=["Protocol Generation"],
)
app.include_router(
    protocol_generation_assigner_router,
    prefix=ENDPOINTS_PREFIX,
    tags=["Protocol Generation"],
)
app.include_router(
    single_protocol_file_generation_router,
    prefix=ENDPOINTS_PREFIX,
    tags=["Single Protocol File Generation"],
)


# Protocol Check ###############################################################

app.include_router(
    protocol_check_router, prefix=ENDPOINTS_PREFIX, tags=["Protocol Check"]
)


# Protocol Debug ###############################################################
app.include_router(
    protocol_debug_router, prefix=ENDPOINTS_PREFIX, tags=["Protocol Debug"]
)


# Paper Generation ###############################################################
app.include_router(
    paper_generation_router, prefix=ENDPOINTS_PREFIX, tags=["Paper Generation"]
)


if WEB_DIST_DIR:

    @app.get("/", include_in_schema=False)
    async def serve_frontend_index():
        return FileResponse(WEB_DIST_DIR / "index.html")


    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_app(full_path: str):
        if full_path.startswith("api/") or full_path in {"docs", "redoc", "openapi.json"}:
            raise HTTPException(status_code=404, detail="Not Found")

        target = WEB_DIST_DIR / full_path
        if target.exists() and target.is_file():
            return FileResponse(target)

        return FileResponse(WEB_DIST_DIR / "index.html")
