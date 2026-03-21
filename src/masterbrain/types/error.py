from pydantic import BaseModel
from typing import Literal


__all__ = [
    "AvailableErrorCode",
    "OPENAI_EXCEPTION_ERROR_CODE_MAPPING",
    "detect_error_codes_in_error_str",
]


AvailableErrorCode = Literal[
    "error_api_connection",  # The API connection is failed.
    "error_api_permission_denied",  # Due to VPN and other reasons, the API connection is denied.
    "error_api_timeout",  # The API request times out.
    "error_max_tokens",  # The max_tokens is too large and exceeds the limit.
    "error_rate_limit",  # The API request is rate limited. Request too many tokens in a short time.
    "error_function_name",  # The function name is not available.
]


OPENAI_EXCEPTION_ERROR_CODE_MAPPING: dict[str, AvailableErrorCode] = {
    # key: error code pattern
    # value: error code
    "APIConnectionError": "error_api_connection",
    "PermissionDeniedError": "error_api_permission_denied",
    "APITimeoutError": "error_api_timeout",
    "maximum context length": "error_max_tokens",
    "RateLimitError": "error_rate_limit",
}


def detect_error_codes_in_error_str(
    error_str: str, error_code_mapping: dict[str, AvailableErrorCode]
) -> list[AvailableErrorCode]:
    """
    Detect the error codes in the error string.
    """
    error_codes = set()
    for error_code_pattern, error_code in error_code_mapping.items():
        if error_code_pattern in error_str:
            error_codes.add(error_code)
    return sorted(list(error_codes))


__all__ = [
    "LlmError",
]


class LlmError(BaseModel):
    """
    The error response of the large language model.
    """

    error: str
    error_codes: list[AvailableErrorCode]
    """
    Provide the standardized error codes to allow the front-end to easily handle the error.
    """
