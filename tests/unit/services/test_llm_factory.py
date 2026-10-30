import pytest
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from homewellness.services.llm_factory import DEFAULT_MODELS, build_chat_model
from homewellness.services.scripted_model import ScriptedChatModel
from homewellness.settings import Settings


def make(**fields):
    return Settings(store_backend="memory", **fields)


def should_build_the_offline_model_when_the_provider_is_fake():
    assert isinstance(build_chat_model(make()), ScriptedChatModel)


def should_build_claude_with_the_default_model_and_limits():
    model = build_chat_model(make(llm_provider="anthropic", anthropic_api_key="k"))
    assert isinstance(model, ChatAnthropic)
    assert (model.model, model.max_tokens, model.default_request_timeout, model.max_retries) == (
        "claude-haiku-5-5", 512, 30.0, 1)


def should_use_the_model_name_from_the_settings_when_one_is_set():
    model = build_chat_model(make(llm_provider="anthropic", anthropic_api_key="k",
                                  llm_model="claude-sonnet-5-5", llm_timeout_seconds=9.0))
    assert (model.model, model.default_request_timeout) == ("claude-sonnet-5-5", 9.0)


def should_build_openai_on_the_chat_completions_api_with_the_default_model():
    model = build_chat_model(make(llm_provider="openai", openai_api_key="k"))
    assert isinstance(model, ChatOpenAI)
    assert model.model_name == DEFAULT_MODELS["openai"] == "gpt-5.4-mini"
    assert model.use_responses_api is False and model.openai_api_base is None


def should_build_openrouter_with_the_nemotron_model_and_the_router_url():
    model = build_chat_model(make(llm_provider="openrouter", openrouter_api_key="k"))
    assert model.model_name == "nvidia/nemotron-3-ultra-550b-a55b:free"
    assert model.openai_api_base == "https://openrouter.ai/api/v1"
    assert model.use_responses_api is False and model.max_retries == 1


def should_use_the_router_url_from_the_settings_when_one_is_set():
    model = build_chat_model(make(llm_provider="openrouter", openrouter_api_key="k",
                                  openrouter_base_url="http://localhost:9/v1"))
    assert model.openai_api_base == "http://localhost:9/v1"


def should_send_a_temperature_only_when_one_is_set():
    # NOTE: LangChain drops the temperature for reasoning models such as gpt-5. Use another model.
    fields = {"llm_provider": "openrouter", "openrouter_api_key": "k"}
    plain = build_chat_model(make(**fields))
    warm = build_chat_model(make(**fields, llm_temperature=0.3))
    assert (plain.temperature, warm.temperature) == (None, 0.3)


@pytest.mark.parametrize(("provider", "variable"), [
    ("anthropic", "ANTHROPIC_API_KEY"), ("openai", "OPENAI_API_KEY"),
    ("openrouter", "OPENROUTER_API_KEY")])
def should_name_the_missing_variable_when_the_key_is_not_set(provider, variable):
    with pytest.raises(ValueError, match=variable):
        build_chat_model(make(llm_provider=provider))


def should_raise_value_error_when_the_provider_is_not_implemented():
    with pytest.raises(ValueError, match="gpt"):
        build_chat_model(make(llm_provider="gpt"))


@pytest.mark.parametrize("provider", ["anthropic", "openai", "openrouter"])
def should_not_show_the_key_when_the_model_is_printed(provider):
    fields = {"llm_provider": provider, f"{provider}_api_key": "secret-key-123"}
    assert "secret-key-123" not in repr(build_chat_model(make(**fields)))
