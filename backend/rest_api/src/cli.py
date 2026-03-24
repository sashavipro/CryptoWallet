"""rest_api/cli.py."""

import asyncio
import logging
import uuid

import click

from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import UserGateway
from src.application.ports.utils import PasswordHasher
from src.domain.entities import User
from src.domain.value_objects.user import RawPassword
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
    """Create a default superuser (or administrator)."""

    async def _run():
        container = create_container()

        async with container() as request_container:
            user_gateway = await request_container.get(UserGateway)
            uow = await request_container.get(UnitOfWork)
            password_hasher = await request_container.get(PasswordHasher)

            if await user_gateway.get_user_by_email(email):
                click.echo(
                    click.style(f"User with email {email} already exists.", fg="yellow")
                )
                return

            click.echo(f"Creating superuser {username} ({email})...")

            try:
                valid_password = RawPassword(password)
                hashed_password = password_hasher.hash(valid_password.value)

                new_user = User(
                    id=uuid.uuid4(),
                    email=email,
                    username=username,
                    password_hash=hashed_password,
                    is_active=True,
                    avatar_url=None,
                )

                async with uow:
                    await user_gateway.add_user(new_user)

                click.echo(click.style("Superuser created successfully!", fg="green"))

            except Exception as e:  # noqa: BLE001
                click.echo(click.style(f"Failed to create superuser: {e}", fg="red"))

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
