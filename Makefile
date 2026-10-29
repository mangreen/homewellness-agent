# All Python work runs in Docker. The host needs only Docker and git.
.PHONY: up down ps logs test itest uitest rehearse open lint sim say alerts demo-cli openapi demo-reset offline-bundle

up:
	test -f .env || cp .env.example .env
	docker compose up -d --build
	docker compose ps

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=100

test:
	test -f .env || cp .env.example .env
	docker compose --profile test build test
	docker compose --profile test run --rm test

itest:
	test -f .env || cp .env.example .env
	docker compose --profile test build itest
	docker compose --profile test run --rm itest

# Play a demo scenario: make sim S=morning   (morning | dizzy | crisis)
sim:
	docker compose exec app python -m homewellness.simulator $(S)

# Talk to the agent: make say T="我今天頭有點暈"
say:
	curl -s -X POST http://localhost:8001/elders/demo-elder-001/messages \
		-H 'Content-Type: application/json' -H "Idempotency-Key: $$(uuidgen)" \
		-d '{"text": "$(T)"}'; echo

alerts:
	curl -s http://localhost:8001/alerts; echo

# The whole story in the terminal. Needs no other container and no network. Add ARGS=--step to pause.
demo-cli:
	test -f .env || cp .env.example .env
	docker compose build app
	docker compose run --rm --no-deps app python -m homewellness.demo_cli $(ARGS)

# Rewrite docs/api/openapi.yaml after an API change.
openapi:
	test -f .env || cp .env.example .env
	docker compose --profile test build test
	docker compose --profile test run --rm -T test python -m homewellness.api.export_openapi > docs/api/openapi.yaml

# Clear the in-memory database and the de-duplication keys. Then replay the scenarios.
demo-reset:
	docker compose restart dynamodb app

uitest:
	docker compose --profile test build uitest
	docker compose --profile test run --rm uitest

# Play the whole story through the real page against the running stack (about 30 seconds).
rehearse:
	test -f .env || cp .env.example .env
	docker compose --profile test build rehearse
	docker compose --profile test run --rm rehearse

open:
	open http://localhost:8501

lint:
	test -f .env || cp .env.example .env
	docker compose --profile test build test
	docker compose --profile test run --rm test ruff check .

# Save images for offline restore: docker load -i dist/homewellness-images.tar
offline-bundle:
	mkdir -p dist
	docker save -o dist/homewellness-images.tar \
		$${MOSQUITTO_IMAGE:-eclipse-mosquitto:2.0.18} \
		$${DYNAMODB_IMAGE:-amazon/dynamodb-local:2.5.2} \
		homewellness-app homewellness-test homewellness-ui
