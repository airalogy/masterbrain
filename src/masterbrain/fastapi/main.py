"""
Main file for FastAPI server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from masterbrain.endpoints import (
    chat_qa_language_router,
    chat_qa_stt_router,
    chat_qa_vision_router,
    field_input_router,
    paper_generation_router,
    protocol_check_router,
    protocol_debug_router,
    protocol_generation_aimd_router,
    protocol_generation_assigner_router,
    protocol_generation_model_router,
    single_protocol_file_generation_router,
)
from masterbrain.endpoints.aira.router import aira_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ENDPOINTS_PREFIX = "/api/endpoints"


# AIRA #########################################################################
app.include_router(aira_router, prefix=ENDPOINTS_PREFIX, tags=["AIRA"])


# Chat #########################################################################
app.include_router(chat_qa_language_router, prefix=ENDPOINTS_PREFIX, tags=["Chat"])
app.include_router(chat_qa_vision_router, prefix=ENDPOINTS_PREFIX, tags=["Chat"])
app.include_router(chat_qa_stt_router, prefix=ENDPOINTS_PREFIX, tags=["Chat"])
app.include_router(field_input_router, prefix=ENDPOINTS_PREFIX, tags=["Chat"])


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
