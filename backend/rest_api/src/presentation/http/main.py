"""rest_api/src/presentation/http/main.py."""

from fastapi import FastAPI

from src.infrastructure.log_config import setup_logging

setup_logging()

app = FastAPI()
