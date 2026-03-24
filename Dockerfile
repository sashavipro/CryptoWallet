FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY backend/rest_api/pyproject.toml backend/rest_api/poetry.lock* /app/backend/rest_api/

WORKDIR /app/backend/rest_api
RUN poetry install --no-root --no-interaction --no-ansi

WORKDIR /app
COPY . /app/

ENV PYTHONPATH=/app/backend/rest_api

CMD ["uvicorn", "src.presentation.http.main:app", "--host", "0.0.0.0", "--port", "8000"]
