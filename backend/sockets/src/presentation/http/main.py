"""sockets/src/presentation/http/main.py."""

import asyncio
import logging
from contextlib import asynccontextmanager

import socketio
from dishka.integrations.faststream import setup_dishka as setup_dishka_faststream
from fastapi import FastAPI
from faststream import FastStream

from src.infrastructure.message_broker.broker import broker
from src.ioc.container import create_container
from src.presentation.amqp.consumers import router as amqp_router
from src.presentation.ws.namespaces import ChatNamespace
from src.presentation.ws.namespaces import TransactionNamespace
from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
MAX_RETRIES = 5

container = create_container()
sio.register_namespace(ChatNamespace("/chat", container=container))
sio.register_namespace(TransactionNamespace("/transaction", container=container))

broker.include_router(amqp_router)

faststream_app = FastStream(broker)
setup_dishka_faststream(container, faststream_app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the FastAPI app lifespan and handle the broker connection with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            await broker.start()
            logger.info("Successfully connected to RabbitMQ!")
            break
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                logger.exception(
                    "Failed to connect to RabbitMQ after %s attempts.", MAX_RETRIES
                )
                raise
            logger.warning("RabbitMQ is not ready yet, retrying in 5s... Error: %s", e)
            await asyncio.sleep(5)

    yield
    await broker.close()


fastapi_app = FastAPI(title="Socket Service", lifespan=lifespan)


@fastapi_app.get("/health")
def healthcheck():
    """Health check endpoint to verify the service status."""
    return {"status": "ok"}


app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=fastapi_app)
