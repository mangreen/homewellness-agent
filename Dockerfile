# NOTE: Debian 12 (bookworm) is pinned for compatibility with Docker Engine 20.10.
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests
# One process only: the clock, the alert list and the MQTT subscriber live in it.
CMD ["uvicorn", "homewellness.main:create_production_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
