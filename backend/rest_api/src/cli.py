"""rest_api/src/cli.py."""

import asyncio
import logging
import uuid

import click
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from src.application.ports.gateways import AssetGateway
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import UserGateway
from src.application.ports.utils import PasswordHasher
from src.domain.entities import Asset
from src.domain.entities import User
from src.domain.value_objects.asset.asset_type import AssetType
from src.infrastructure.settings import MongoSettings
from src.infrastructure.settings import SecuritySettings
from src.infrastructure.utils.aes_encryptor import AesEncryptor
from src.ioc.container import create_container

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Command line utilities for CryptoWallet API."""


@cli.command()
@click.option("--email", default="admin@admin.com", help="Superuser email")
@click.option("--username", default="admin", help="Superuser username")
@click.option("--password", default="Admin12345", help="Superuser password")
def create_superuser(email, username, password):
    """Create a default superuser in the main database."""

    async def _run():
        container = create_container()
        async with container() as request_container:
            user_gateway = await request_container.get(UserGateway)
            uow = await request_container.get(UnitOfWork)
            password_hasher = await request_container.get(PasswordHasher)

            if await user_gateway.get_user_by_email(email):
                click.echo(click.style(f"User {email} already exists.", fg="yellow"))
                return

            hashed_password = password_hasher.hash(password)
            new_user = User(
                id=uuid.uuid4(),
                email=email,
                username=username,
                password_hash=hashed_password,
            )
            async with uow:
                await user_gateway.add_user(new_user)
            click.echo(click.style("Superuser created successfully!", fg="green"))

    asyncio.run(_run())


@cli.command()
def seed_assets():
    """Seed initial assets (like ETH) into the rest_api database."""

    async def _run():
        container = create_container()
        async with container() as request_container:
            asset_gateway = await request_container.get(AssetGateway)
            uow = await request_container.get(UnitOfWork)

            all_assets = await asset_gateway.get_all_assets()
            existing = any(
                a.ticker == "ETH" and a.network == "sepolia" for a in all_assets
            )

            if existing:
                click.echo("Asset 'ETH' already exists. Skipping.")
                return

            new_eth = Asset(
                id=uuid.uuid4(),
                network="sepolia",
                asset_type=AssetType.NATIVE,
                name="Ethereum",
                ticker="ETH",
                decimals=18,
            )
            async with uow:
                await asset_gateway.add_asset(new_eth)
            click.echo(click.style("Successfully seeded asset 'ETH'", fg="green"))

    asyncio.run(_run())


@cli.command()
@click.argument("secret")
def encrypt(secret: str):
    """Encrypt a secret string (like a private key) for .env."""
    try:
        settings = SecuritySettings()
        encryptor = AesEncryptor(settings)
        encrypted_value = encryptor.encrypt(secret)
        click.echo(click.style(f"Encrypted key: {encrypted_value}", fg="green"))
    except Exception as e:  # noqa: BLE001
        click.echo(click.style(f"Error: {e}", fg="red"))


@cli.command()
def init_mongo():
    """Initialize MongoDB: create collections and build indexes."""

    async def _run():
        settings = MongoSettings()
        client = AsyncIOMotorClient(settings.mongo_url)
        db = client[settings.MONGO_DB]

        click.echo("Initializing MongoDB indexes...")

        try:
            await db["chat_messages_mongo"].create_index(
                [("created_at", pymongo.DESCENDING)],
                name="idx_created_at_desc",
                background=True,
            )
            click.echo(
                click.style(
                    "✓ Index on chat_messages_mongo (created_at) created.", fg="green"
                )
            )

            await db["chat_messages_mongo"].create_index(
                [("user_id", pymongo.ASCENDING)], name="idx_user_id", background=True
            )
            click.echo(
                click.style(
                    "✓ Index on chat_messages_mongo (user_id) created.", fg="green"
                )
            )

        except PyMongoError as e:
            click.echo(click.style(f"Error initializing MongoDB: {e}", fg="red"))
        finally:
            client.close()

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
