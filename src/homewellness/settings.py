"""Settings from environment variables (12-factor). Keys are read here and never logged."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

_BACKENDS = ("dynamodb", "memory")
LLM_PROVIDERS = ("fake", "anthropic", "openai", "openrouter")
_TRUE = {"1", "true", "yes"}
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1"


def _text(env: Mapping[str, str], name: str) -> str | None:
    """Return the trimmed value, or None when the variable is missing or blank."""
    value = env.get(name, "").strip()
    return value or None


@dataclass(frozen=True, slots=True)
class Settings:
    store_backend: str = "dynamodb"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    dynamodb_endpoint: str | None = None  # None means the real AWS endpoint.
    dynamodb_table: str = "homewellness"
    aws_region: str = "ap-northeast-1"
    log_level: str = "INFO"
    demo_mode: bool = False
    # Agent brain. "fake" runs offline. The others need a key and a network.
    llm_provider: str = "fake"
    llm_model: str | None = None  # None means the default model of the provider.
    llm_timeout_seconds: float = 30.0
    llm_temperature: float | None = None  # None: the provider decides.
    llm_fallback: bool = True  # On a provider failure, answer with the offline model.
    openrouter_base_url: str = DEFAULT_OPENROUTER_URL
    # NOTE: repr=False keeps the keys out of logs and error messages.
    anthropic_api_key: str | None = field(default=None, repr=False)
    openai_api_key: str | None = field(default=None, repr=False)
    openrouter_api_key: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        backend = env.get("STORE_BACKEND", "dynamodb")
        if backend not in _BACKENDS:
            raise ValueError(f"STORE_BACKEND must be one of {_BACKENDS}, not {backend!r}")
        provider = env.get("LLM_PROVIDER", "fake").strip().lower() or "fake"
        if provider not in LLM_PROVIDERS:
            raise ValueError(f"LLM_PROVIDER must be one of: {', '.join(LLM_PROVIDERS)}")
        timeout = float(env.get("LLM_TIMEOUT_SECONDS", "30") or "30")
        if timeout <= 0:
            raise ValueError("LLM_TIMEOUT_SECONDS must be above 0")
        temperature = _text(env, "LLM_TEMPERATURE")
        return cls(
            store_backend=backend,
            mqtt_host=env.get("MQTT_HOST", "localhost"),
            mqtt_port=int(env.get("MQTT_PORT", "1883")),
            dynamodb_endpoint=env.get("DYNAMODB_ENDPOINT") or None,
            dynamodb_table=env.get("DYNAMODB_TABLE", "homewellness"),
            aws_region=env.get("AWS_REGION", "ap-northeast-1"),
            log_level=env.get("LOG_LEVEL", "INFO"),
            demo_mode=env.get("DEMO_MODE", "false").strip().lower() in _TRUE,
            llm_provider=provider,
            llm_model=_text(env, "LLM_MODEL"),
            llm_timeout_seconds=timeout,
            llm_temperature=float(temperature) if temperature is not None else None,
            llm_fallback=env.get("LLM_FALLBACK", "true").strip().lower() in _TRUE,
            openrouter_base_url=_text(env, "OPENROUTER_BASE_URL") or DEFAULT_OPENROUTER_URL,
            anthropic_api_key=_text(env, "ANTHROPIC_API_KEY"),
            openai_api_key=_text(env, "OPENAI_API_KEY"),
            openrouter_api_key=_text(env, "OPENROUTER_API_KEY"),
        )
