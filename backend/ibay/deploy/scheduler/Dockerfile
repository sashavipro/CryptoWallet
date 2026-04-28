FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir poetry

WORKDIR /app/backend/ibay
COPY backend/ibay/pyproject.toml backend/ibay/poetry.lock* ./
RUN poetry install --no-root --no-interaction --no-ansi

WORKDIR /app
COPY . /app/

ENV PYTHONPATH=/app/backend/ibay

CMD ["taskiq", "scheduler", "src.infrastructure.task_broker:scheduler", "src.application.tasks.delivery"]
