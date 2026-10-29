# All Python work runs in Docker. The host needs only Docker and git.
.PHONY: up down ps logs test itest lint sim demo-reset offline-bundle

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

# Clear the in-memory database and the de-duplication keys. Then replay the scenarios.
demo-reset:
	docker compose restart dynamodb app

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
		homewellness-app homewellness-test
