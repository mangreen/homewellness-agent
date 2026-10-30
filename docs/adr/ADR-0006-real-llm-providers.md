# ADR-0006: Real LLM Providers behind a Factory, with an Offline Fallback

Date: 2026-10-29
Status: Accepted

## Context
The demo runs offline with a scripted model (ADR-0004-offline-agent-and-http-api.md). The user wants to choose a real LLM
(Claude, OpenAI or OpenRouter, for example `nvidia/nemotron-3-ultra-550b-a55b:free`) when a key and a network exist.
A real model talks freely, can fail, and sends data to a third party. The safety design must not depend on the model.

## Decision
- `LLM_PROVIDER` is one of `fake` (default), `anthropic`, `openai`, `openrouter`. `services/llm_factory.py` builds the chat model.
- Keys come from `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`. A missing key stops the start-up with a clear message.
  Keys are hidden from `repr`, logs and errors. LangChain tracing stays off.
- Defaults: `claude-haiku-5-5`, `gpt-5.4-mini`, `nvidia/nemotron-3-ultra-550b-a55b:free`. `LLM_MODEL` overrides them.
- OpenAI and OpenRouter use the same client on the chat-completions API. OpenRouter adds its base URL.
- The timeout is 30 seconds and there is one retry. A temperature is sent only when `LLM_TEMPERATURE` is set.
- `LLM_FALLBACK=true` (default for real providers): when the provider fails, the offline model answers that request. The activity timeline shows it.
- The prompt tells a real model when to call each tool, to answer in Traditional Chinese in short words, and not to claim an alert that was not sent.
- Tools, the alert policy, idempotency and the tool binding to one elder do not change.
- `GET /demo/brain` and the page show the active brain. The page warns when data leaves the machine.
- `make llm-eval` runs nine fixed cases against the chosen brain. It turns the fallback off.

## Alternatives Considered
- **One provider only.** Simpler. The user asked for three, and OpenAI-compatible servers share one client.
- **OpenRouter for everything.** One key. It adds a hop, and free models are less reliable. Kept as one option only.
- **`init_chat_model("provider:model")`.** Shorter. It hides the options (timeout, base URL, headers) that we need to control.
- **`with_fallbacks` of LangChain.** The wrapper has no `bind_tools`, so `create_agent` cannot use it. The fallback is a runner instead.
- **Choose the provider in the page.** Keys would pass through the browser. Rejected. Use `.env`.
- **Amazon Bedrock.** Fits the AWS story. Needs AWS credentials and model access. A next step.

## [Trade-off Analysis]
- Pros: the demo can show a real LLM. Offline stays the default. Safety stays in code. A network or rate-limit failure does not stop the demo.
- Cons: answers vary between runs. Free models can lack tool support or be slow. Model names change. The image has more packages.
- Reason: the architecture was built for this swap. The fallback and the evaluation keep the risk small. A formal demo should still use the offline model.

## Consequences
- Conversation data and health values go to the provider. The demo elder is fictional. A free endpoint can log prompts.
- A fallback can hide a provider problem, so the evaluation turns it off.
- The OpenAI path drops `temperature` for reasoning models such as `gpt-5` (LangChain does it).

## Verification
481 unit tests pass. A fake OpenAI-compatible server drives the whole tool loop for OpenAI and OpenRouter (URL, key header, body, tools).
A real call to the Anthropic endpoint with an invalid key gave an authentication error, the fallback answered in about 3 seconds, and no key was logged.
Not verified: a successful call with a real key. The user runs `make llm-eval` with a key and a network.

Related: MEM-0006-real-llm-providers.md, ADR-0004-offline-agent-and-http-api.md
