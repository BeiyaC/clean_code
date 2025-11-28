from dataclasses import dataclass, field
from typing import Tuple

from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core import ms_config
from app.core.config import BaseConfig, Database
from app.repositories.base_sql_repository import transaction as base_transaction


def create_engine(database: Database, config: BaseConfig) -> Tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        URL.create(
            drivername="postgresql+asyncpg",
            username=database.user,
            password=database.password,
            host=database.host,
            port=database.port,
            database=database.database,
        ),
        pool_pre_ping=True,
        echo=config.is_dev_environment(),
    )
    Session = async_sessionmaker(bind=engine, expire_on_commit=False)

    return engine, Session


engine, Session = create_engine(ms_config.database, ms_config)


@dataclass
class transaction(base_transaction):
    session_maker: async_sessionmaker[AsyncSession] = field(default=Session, init=False)
