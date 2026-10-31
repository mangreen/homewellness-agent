"""Turn a provider error into a short text with a hint. Used by the evaluation and the probe.

NOTE: The text can hold the message of the provider. It never holds a key: anything that looks
like a key is removed. The runtime log keeps only the error type and the status code.
"""

import re

_SECRET = re.compile(r"(Bearer\s+\S+|sk-[A-Za-z0-9_-]{8,})")
_LIMIT = 300


def _hint(status: int | None, message: str, type_name: str) -> str:
    text = message.lower()
    if status in (401, 403):
        return "The key was rejected. Check the key and the account."
    if status == 402:
        return "The account needs credits."
    if status == 404:
        if "data policy" in text:
            return ("OpenRouter blocks this free model by your privacy settings. "
                    "Open https://openrouter.ai/settings/privacy and allow free endpoints.")
        if "tool" in text:
            return "This model or endpoint cannot call tools. Choose another model with LLM_MODEL."
        return "The model name was not found, or no provider serves it now. Check LLM_MODEL."
    if status == 429:
        return ("Rate limit. Free models have limits per minute and per day. "
                "Wait, use --delay, or use a paid model.")
    if status in (400, 422):
        return "The provider rejected the request. The model may not accept tools or some options."
    if status is not None and status >= 500:
        return "Provider error. Try again, or choose another model."
    if "Timeout" in type_name:
        return "The request timed out. Raise LLM_TIMEOUT_SECONDS or choose a faster model."
    if "Connection" in type_name:
        return "No connection to the provider. Check the network and the DNS of Docker."
    return ""


def explain_llm_error(error: BaseException) -> str:
    status = getattr(error, "status_code", None)
    message = _SECRET.sub("[redacted]", str(getattr(error, "message", "") or error))[:_LIMIT]
    name = type(error).__name__
    head = f"{name} (HTTP {status}): {message}" if status else f"{name}: {message}"
    hint = _hint(status, message, name)
    return f"{head.rstrip('.')}. Hint: {hint}" if hint else head
