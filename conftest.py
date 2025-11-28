import asyncio
from functools import lru_cache

import pytest
import pytest_asyncio
from alembic import command
from alembic import config as alembic_config
from alembic.util import immutabledict
from httpx import ASGITransport, AsyncClient
from app.repositories.base_sql_repository import SqlBaseRepository
from app.core.sql import truncate_all_tables
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

from app.core import ms_config
from app.core.db import Session, engine
from main import app

DROP_AUTHORIZATION_DATABASE = """
DROP DATABASE IF EXISTS clean_code_test;
"""

CREATE_AUTHORIZATION_DATABASE = """
CREATE DATABASE clean_code_test;
"""


@lru_cache
def is_integration_test_suite(markers):
    return not markers or ("integration" in markers and "not integration" not in markers)


def pytest_collection_modifyitems(items):
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unittest)


@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True, scope="session")
async def create_database_if_not_exists(pytestconfig):
    markers = pytestconfig.getoption("-m")
    if not is_integration_test_suite(markers):
        yield
        return

    postgres_engine_url = URL(
        drivername="postgresql+asyncpg",
        username=ms_config.database.user,
        password=ms_config.database.password,
        host=ms_config.database.host,
        port=ms_config.database.port,
        query=immutabledict(),
        database="postgres",
    )

    postgres_engine = create_async_engine(postgres_engine_url, pool_pre_ping=True, echo=False)

    async with postgres_engine.connect() as conn:
        await conn.execute(text("COMMIT"))
        await conn.execute(text(DROP_AUTHORIZATION_DATABASE))
        await conn.execute(text(CREATE_AUTHORIZATION_DATABASE))
    yield


def run_migrations(connection, cfg):
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


@pytest_asyncio.fixture(autouse=True, scope="session")
async def run_async_migrations():
    async with engine.begin() as conn:
        await conn.run_sync(run_migrations, alembic_config.Config("alembic.ini"))


@pytest_asyncio.fixture(autouse=True, scope="function")
async def cleanup_database_tables(pytestconfig):
    yield
    markers = pytestconfig.getoption("-m")
    if not is_integration_test_suite(markers):
        return
    async with engine.connect() as con:
        await con.execute(text(truncate_all_tables))
        await con.execute(text("select truncate_tables();"))
        await con.commit()


@pytest_asyncio.fixture
async def factory(request):
    repo = SqlBaseRepository(Session)
    objs = [obj for obj in request.param]
    for obj in objs:
        if isinstance(obj, list):
            await repo.create_all(obj)
        else:
            await repo.create_or_update(obj)
    yield objs


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as ac:
        yield ac