"""Settings from environment variables (12-factor). No secret is read or stored here."""

import os
from collections.abc import Mapping
from dataclasses import dataclass

_BACKENDS = ("dynamodb", "memory")
_TRUE = {"1", "true", "yes"}


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
    health_port: int = 8000

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        backend = env.get("STORE_BACKEND", "dynamodb")
        if backend not in _BACKENDS:
            raise ValueError(f"STORE_BACKEND must be one of {_BACKENDS}, not {backend!r}")
        return cls(
            store_backend=backend,
            mqtt_host=env.get("MQTT_HOST", "localhost"),
            mqtt_port=int(env.get("MQTT_PORT", "1883")),
            dynamodb_endpoint=env.get("DYNAMODB_ENDPOINT") or None,
            dynamodb_table=env.get("DYNAMODB_TABLE", "homewellness"),
            aws_region=env.get("AWS_REGION", "ap-northeast-1"),
            log_level=env.get("LOG_LEVEL", "INFO"),
            demo_mode=env.get("DEMO_MODE", "false").strip().lower() in _TRUE,
            health_port=int(env.get("HEALTH_PORT", "8000")),
        )
