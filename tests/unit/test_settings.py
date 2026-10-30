import pytest

from homewellness.settings import Settings


def should_use_safe_defaults_when_the_environment_is_empty():
    settings = Settings.from_env({})
    assert (settings.store_backend, settings.mqtt_host, settings.mqtt_port) == (
        "dynamodb", "localhost", 1883)
    assert (settings.demo_mode, settings.dynamodb_endpoint) == (False, None)


def should_use_the_fake_llm_when_no_provider_is_set():
    assert Settings.from_env({}).llm_provider == "fake"


def should_read_values_when_the_environment_sets_them():
    settings = Settings.from_env({
        "STORE_BACKEND": "memory", "MQTT_HOST": "broker", "MQTT_PORT": "1884",
        "DYNAMODB_ENDPOINT": "http://dynamodb:8000", "DEMO_MODE": "true", "LOG_LEVEL": "DEBUG",
    })
    assert (settings.store_backend, settings.mqtt_host) == ("memory", "broker")
    assert settings.mqtt_port == 1884
    assert (settings.dynamodb_endpoint, settings.demo_mode, settings.log_level) == (
        "http://dynamodb:8000", True, "DEBUG")


@pytest.mark.parametrize(
    ("text", "expected"),
    [("true", True), ("TRUE", True), ("1", True), ("yes", True),
     ("false", False), ("0", False), ("", False)],
)
def should_parse_demo_mode_when_the_value_is_a_boolean_text(text, expected):
    assert Settings.from_env({"DEMO_MODE": text}).demo_mode is expected


def should_raise_value_error_when_the_store_backend_is_unknown():
    with pytest.raises(ValueError):
        Settings.from_env({"STORE_BACKEND": "oracle"})


def should_raise_value_error_when_the_port_is_not_a_number():
    with pytest.raises(ValueError):
        Settings.from_env({"MQTT_PORT": "abc"})


def should_use_safe_llm_defaults_when_nothing_is_set():
    s = Settings.from_env({})
    assert (s.llm_model, s.llm_timeout_seconds, s.llm_temperature, s.llm_fallback) == (
        None, 30.0, None, True)
    assert (s.anthropic_api_key, s.openai_api_key, s.openrouter_api_key) == (None, None, None)
    assert s.openrouter_base_url == "https://openrouter.ai/api/v1"


def should_read_the_llm_options_when_the_environment_sets_them():
    s = Settings.from_env({
        "LLM_PROVIDER": " OpenRouter ", "LLM_MODEL": "vendor/model:free",
        "LLM_TIMEOUT_SECONDS": "12.5", "LLM_TEMPERATURE": "0.2", "LLM_FALLBACK": "false",
        "OPENROUTER_API_KEY": "k-or", "OPENROUTER_BASE_URL": "http://localhost:9/v1",
        "OPENAI_API_KEY": "k-oa", "ANTHROPIC_API_KEY": "k-an",
    })
    assert (s.llm_provider, s.llm_model, s.llm_timeout_seconds) == (
        "openrouter", "vendor/model:free", 12.5)
    assert (s.llm_temperature, s.llm_fallback) == (0.2, False)
    assert (s.openrouter_api_key, s.openai_api_key, s.anthropic_api_key) == ("k-or", "k-oa", "k-an")
    assert s.openrouter_base_url == "http://localhost:9/v1"


def should_treat_an_empty_value_as_not_set_when_the_environment_has_a_blank_key():
    s = Settings.from_env({"ANTHROPIC_API_KEY": "", "LLM_MODEL": "  ", "LLM_TEMPERATURE": ""})
    assert (s.anthropic_api_key, s.llm_model, s.llm_temperature) == (None, None, None)


def should_not_show_the_keys_when_the_settings_are_printed():
    s = Settings(anthropic_api_key="secret-aaa", openai_api_key="secret-bbb",
                 openrouter_api_key="secret-ccc")
    assert "secret" not in repr(s) and "secret" not in str(s)


def should_raise_value_error_that_lists_the_providers_when_the_provider_is_unknown():
    with pytest.raises(ValueError, match="fake, anthropic, openai, openrouter"):
        Settings.from_env({"LLM_PROVIDER": "gpt"})


@pytest.mark.parametrize("value", ["0", "-3", "abc"])
def should_raise_value_error_when_the_timeout_is_not_a_positive_number(value):
    with pytest.raises(ValueError):
        Settings.from_env({"LLM_TIMEOUT_SECONDS": value})
