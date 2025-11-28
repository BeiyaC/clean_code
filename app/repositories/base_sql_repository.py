from contextlib import AsyncContextDecorator, asynccontextmanager
from contextvars import ContextVar
from copy import copy
from dataclasses import dataclass, field
from typing import Any, List, TypeVar

from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.selectable import TypedReturnsRows

from app.models.base_model import Base
from app.models.search_filter_mixin import SearchFilterMixin

T = TypeVar("T", bound=Base)
V = TypeVar("V", bound=Any)

session_ctx: ContextVar[AsyncSession] = ContextVar("session_ctx")


@dataclass
class transaction(AsyncContextDecorator):
    session_maker: async_sessionmaker[AsyncSession]
    allowed_exceptions: list[type[Exception]] = field(default_factory=list)

    def _recreate_cm(self):
        return copy(self)

    async def __aenter__(self):
        self.session = self.session_maker()
        self.ctx = session_ctx.set(self.session)

    async def __aexit__(self, exc_type: type[Exception] | None, exc_value: Exception | None, traceback):
        if exc_type is None or exc_type in self.allowed_exceptions:
            await self.session.commit()
        else:
            await self.session.rollback()
        await self.session.close()
        session_ctx.reset(self.ctx)


@dataclass
class SqlBaseRepository(SearchFilterMixin):
    db: async_sessionmaker[AsyncSession]

    async def create_or_update(self, model: T):  # pyright: ignore [reportInvalidTypeVarUse]
        async with self._get_session() as session:
            session.add(model)

    async def delete(self, model: T):  # pyright: ignore [reportInvalidTypeVarUse]
        async with self._get_session() as session:
            await session.delete(model)

    async def create_all(self, models: List[T]):
        async with self._get_session() as session:
            session.add_all(models)

    async def commit(self):
        async with self._get_session() as session:
            await session.commit()

    async def rollback(self):
        async with self._get_session() as session:
            await session.rollback()

    @asynccontextmanager
    async def _get_session(self):
        try:
            yield session_ctx.get()
        except LookupError:
            async with self.db() as session:
                yield session
                await session.commit()

    async def _exec_statement(self, stmt: TypedReturnsRows[V]) -> Result[V]:
        async with self._get_session() as session:
            return await session.execute(stmt)
