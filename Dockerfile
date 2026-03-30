FROM python:3.12-slim

ARG SERVICE_NAME=rest_api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY backend/${SERVICE_NAME}/pyproject.toml backend/${SERVICE_NAME}/poetry.lock* /app/backend/${SERVICE_NAME}/

WORKDIR /app/backend/${SERVICE_NAME}
RUN poetry install --no-root --no-interaction --no-ansi

WORKDIR /app
COPY . /app/

ENV PYTHONPATH=/app/backend/${SERVICE_NAME}

CMD ["uvicorn", "src.presentation.http.main:app", "--host", "0.0.0.0", "--port", "8000"]
