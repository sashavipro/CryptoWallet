FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir poetry

WORKDIR /app/backend/sockets
COPY backend/sockets/pyproject.toml backend/sockets/poetry.lock* ./
RUN poetry install --no-root --no-interaction --no-ansi

WORKDIR /app
COPY . /app/

ENV PYTHONPATH=/app/backend/sockets

CMD ["uvicorn", "src.presentation.http.main:app", "--host", "0.0.0.0", "--port", "8004", "--reload"]
