import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from masterbrain.endpoints.chat.qa.language.router import chat_qa_language_router


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(chat_qa_language_router, prefix="/api/endpoints", tags=["Chat"])
    return TestClient(app)


CLIENT = _build_client()


@pytest.mark.qwen
@pytest.mark.parametrize("enable_thinking", [False, True])
def test_chat_qa_language_stream_first_line_has_content_or_reasoning(enable_thinking):
    payload = {
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": enable_thinking,
            "enable_search": True,
        },
        "messages": [
            {
                "role": "user",
                "content": "Who are you? Please search for Airalogy, then answer what Airalogy is.",
            }
        ],
    }

    # stream the response and collect the full text stream
    with CLIENT.stream("POST", "/api/endpoints/chat/qa/language", json=payload) as resp:
        assert resp.status_code == 200, resp.text
        assert resp.headers.get("content-type", "").startswith("text/plain")

        chunks: list[str] = []
        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = (
                raw_line.decode("utf-8")
                if isinstance(raw_line, (bytes, bytearray))
                else str(raw_line)
            )
            chunks.append(line)

    text = "".join(chunks)
    assert text.strip() != "", "No streamed text content received"

    if enable_thinking:
        assert "<think>" in text
        assert "</think>" in text
        assert text.index("<think>") < text.index("</think>")
        assert text.count("<think>") == text.count("</think>")
    else:
        assert "<think>" not in text
        assert "</think>" not in text
        assert text.count("<think>") == 0 and text.count("</think>") == 0
