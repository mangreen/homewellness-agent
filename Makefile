# All Python work runs in Docker. The host needs only Docker and git.
.PHONY: up down ps logs test lint offline-bundle

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
