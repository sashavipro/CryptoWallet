"""sockets/src/presentation/http/main.py."""

from contextlib import asynccontextmanager

import socketio
from dishka.integrations.faststream import setup_dishka as setup_dishka_faststream
from fastapi import FastAPI
from faststream import FastStream

from src.infrastructure.message_broker.broker import broker
from src.ioc.container import create_container
from src.presentation.amqp.consumers import router as amqp_router
from src.presentation.ws.namespaces.chat import ChatNamespace
from src.presentation.ws.server import sio

container = create_container()
sio.register_namespace(ChatNamespace("/chat", container=container))

broker.include_router(amqp_router)

faststream_app = FastStream(broker)
setup_dishka_faststream(container, faststream_app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the FastAPI app lifespan and handle the broker connection."""
    await broker.start()
    yield
    await broker.close()


fastapi_app = FastAPI(title="Socket Service", lifespan=lifespan)


@fastapi_app.get("/health")
def healthcheck():
    """Health check endpoint to verify the service status."""
    return {"status": "ok"}


app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=fastapi_app)
