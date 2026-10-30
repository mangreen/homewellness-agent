"""Build the chat model of the agent: the offline scripted model or a real LLM.

NOTE: Real providers are imported only when chosen. The offline path needs no key or network.
NOTE: Data sent to a real provider leaves this machine. The demo uses a fictional elder.
"""

from dataclasses import dataclass

import httpx
from langchain_core.language_models.chat_models import BaseChatModel

from homewellness.services.scripted_model import ScriptedChatModel
from homewellness.settings import Settings

DEFAULT_MODELS = {
    "anthropic": "claude-haiku-5-5",  # Low latency. Fits a live demo.
    "openai": "gpt-5.4-mini",  # NOTE: OpenAI renames models often. Set LLM_MODEL if this fails.
    "openrouter": "nvidia/nemotron-3-ultra-550b-a55b:free",
}
_KEY_VARIABLES = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}
_MAX_ANSWER_TOKENS = 512  # Answers are short. Claude requires a limit.


@dataclass(frozen=True, slots=True)
class BrainInfo:
    provider: str
    model: str
    external: bool  # True when conversation data goes to a third party.
    fallback: bool  # True when a failure switches to the offline model.


def describe_brain(settings: Settings) -> BrainInfo:
    if settings.llm_provider == "fake":
        return BrainInfo("fake", "scripted", False, False)
    model = settings.llm_model or DEFAULT_MODELS.get(settings.llm_provider, "")
    return BrainInfo(settings.llm_provider, model, True, settings.llm_fallback)


def _key(settings: Settings) -> str:
    variable = _KEY_VARIABLES[settings.llm_provider]
    key = getattr(settings, f"{settings.llm_provider}_api_key")
    if not key:
        raise ValueError(f"{variable} is not set. LLM_PROVIDER={settings.llm_provider} needs it")
    return key


def build_chat_model(
    settings: Settings, *, http_client: httpx.Client | None = None
) -> BaseChatModel:
    """`http_client` is a test seam for the OpenAI-compatible providers."""
    provider = settings.llm_provider
    if provider == "fake":
        return ScriptedChatModel()
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"LLM_PROVIDER {provider!r} is not implemented")

    model = settings.llm_model or DEFAULT_MODELS[provider]
    options: dict = {"timeout": settings.llm_timeout_seconds, "max_retries": 1}
    if settings.llm_temperature is not None:
        options["temperature"] = settings.llm_temperature

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model, api_key=_key(settings), max_tokens=_MAX_ANSWER_TOKENS,
                             **options)

    from langchain_openai import ChatOpenAI

    if provider == "openrouter":
        options["base_url"] = settings.openrouter_base_url
        options["default_headers"] = {"X-Title": "HomeWellness Companion PoC"}
    return ChatOpenAI(model=model, api_key=_key(settings), use_responses_api=False,
                      http_client=http_client, **options)
