import httpx
from openai import APIConnectionError

from masterbrain.utils import llm


def _make_connection_error(message: str, url: str) -> APIConnectionError:
    request = httpx.Request("POST", url)

    try:
        raise OSError(message)
    except OSError as cause:
        exc = APIConnectionError(request=request)
        exc.__cause__ = cause
        return exc


def test_llm_http_exception_includes_proxy_diagnostics_for_local_proxy(monkeypatch):
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:7897")
    monkeypatch.setenv("https_proxy", "http://127.0.0.1:7897")
    monkeypatch.setenv("all_proxy", "socks5://127.0.0.1:7897")
    monkeypatch.setattr(
        llm,
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    exc = _make_connection_error(
        "Failed to connect to 127.0.0.1 port 7897",
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    )

    http_exc = llm.llm_http_exception(exc, model_name="qwen3.5-flash")

    assert http_exc.status_code == 502
    assert "Masterbrain could not connect to the model provider for `qwen3.5-flash`." in http_exc.detail
    assert "Provider: `qwen`" in http_exc.detail
    assert "Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`" in http_exc.detail
    assert "Underlying error: Failed to connect to 127.0.0.1 port 7897" in http_exc.detail
    assert "http_proxy=http://127.0.0.1:7897" in http_exc.detail
    assert "Detected proxy environment variables pointing to a local proxy." in http_exc.detail


def test_llm_http_exception_flags_invalid_base_url(monkeypatch):
    monkeypatch.delenv("http_proxy", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)
    monkeypatch.delenv("all_proxy", raising=False)
    monkeypatch.setattr(llm, "OPENAI_BASE_URL", "xxx")

    exc = _make_connection_error(
        "Name or service not known",
        "https://api.openai.com/v1/chat/completions",
    )

    http_exc = llm.llm_http_exception(exc, model_name="gpt-4o")

    assert http_exc.status_code == 502
    assert "Provider: `openai`" in http_exc.detail
    assert "Base URL: `xxx`" in http_exc.detail
    assert "Configured base URL `xxx` is not a valid absolute URL." in http_exc.detail
