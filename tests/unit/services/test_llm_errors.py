import httpx
import openai
import pytest

from homewellness.services.llm_errors import explain_llm_error

REQUEST = httpx.Request("POST", "https://provider.example/v1/chat/completions")


def status_error(status, message):
    response = httpx.Response(status, request=REQUEST)
    return openai.APIStatusError(message, response=response, body=None)


@pytest.mark.parametrize(("status", "message", "expected"), [
    (404, "No endpoints found matching your data policy (Free model publication)",
     "openrouter.ai/settings/privacy"),
    (404, "No endpoints found that support tool use", "cannot call tools"),
    (404, "model not found", "LLM_MODEL"),
    (401, "invalid api key", "key was rejected"),
    (403, "forbidden", "key was rejected"),
    (402, "insufficient credits", "credits"),
    (429, "rate limit exceeded", "Rate limit"),
    (400, "bad request", "rejected the request"),
    (503, "upstream error", "Provider error"),
])
def should_explain_the_http_status_with_a_hint(status, message, expected):
    text = explain_llm_error(status_error(status, message))
    assert f"HTTP {status}" in text and message in text and expected in text


def should_name_the_error_type():
    assert explain_llm_error(status_error(404, "x")).startswith("APIStatusError (HTTP 404)")


def should_hint_at_the_timeout_setting_when_the_request_times_out():
    assert "LLM_TIMEOUT_SECONDS" in explain_llm_error(openai.APITimeoutError(request=REQUEST))


def should_hint_at_the_network_when_the_connection_fails():
    text = explain_llm_error(openai.APIConnectionError(request=REQUEST))
    assert "ConnectionError" in text and "network" in text.lower()


def should_give_the_type_and_message_without_a_hint_for_an_unknown_error():
    assert explain_llm_error(KeyError("boom")) == "KeyError: 'boom'"


def should_remove_anything_that_looks_like_a_key():
    # NOTE: Built at run time, so that no key-like text sits in the source.
    token, key = "t" * 12, "sk-" + "a1b2c3d4e5f6"
    text = explain_llm_error(status_error(401, f"bad Bearer {token} and {key}"))
    assert token not in text and key not in text and "[redacted]" in text


def should_cut_a_long_message():
    assert len(explain_llm_error(status_error(500, "x" * 2000))) < 520
