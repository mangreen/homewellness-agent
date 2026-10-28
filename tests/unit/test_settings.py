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
