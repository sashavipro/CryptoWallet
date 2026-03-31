"""ethereum/src/cli.py."""

import asyncio
import uuid

import click
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from src.infrastructure.persistence.database.models.asset import Asset
from src.infrastructure.settings import DatabaseSettings


async def _seed_assets(session: AsyncSession) -> None:
    """Seed initial assets (like ETH) into the database."""
    result = await session.execute(select(Asset).where(Asset.ticker == "ETH"))
    eth_asset = result.scalars().first()

    if eth_asset:
        click.echo("Asset 'ETH' already exists in the database. Skipping.")
        return

    new_eth_asset = Asset(
        id=uuid.uuid4(),
        network="SEPOLIA",
        asset_type="NATIVE",
        name="Ethereum",
        ticker="ETH",
        decimals=18,
    )

    session.add(new_eth_asset)
    await session.commit()
    click.echo(f"Successfully seeded asset 'ETH' with ID: {new_eth_asset.id}")


async def _run_seed() -> None:
    """Set up DB connection and run seeds."""
    db_settings = DatabaseSettings()

    engine = create_async_engine(db_settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as session:
        await _seed_assets(session)

    await engine.dispose()


@click.group()
def cli() -> None:
    """CLI for the Ethereum Microservice."""


@click.command()
def seed() -> None:
    """Seed the database with initial required data (e.g., supported assets)."""
    click.echo("Starting database seed process...")
    asyncio.run(_run_seed())
    click.echo("Seed process finished.")


cli.add_command(seed)

if __name__ == "__main__":
    cli()
