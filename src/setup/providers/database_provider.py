from typing import AsyncGenerator

from dishka import Provider, Scope, from_context, provide
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports import UnitOfWork
from infrastructure.adapters import SQLAlchemyTransaction, UnitOfWorkImpl
from setup.config import Settings
from setup.db_helper import DatabaseHelper


class DatabaseProvider(Provider):
    scope = Scope.APP

    settings = from_context(Settings)

    @provide
    def provide_db(self, settings: Settings) -> DatabaseHelper:
        return DatabaseHelper(
            url=str(settings.db.url),
            echo=settings.db.echo,
            echo_pool=settings.db.echo_pool,
            pool_size=settings.db.pool_size,
            max_overflow=settings.db.max_overflow,
        )

    unit_of_work = provide(
        source=UnitOfWorkImpl,
        provides=UnitOfWork,
        scope=Scope.SESSION,
    )

    @provide(scope=Scope.SESSION)
    async def provide_session(
        self, db_helper: DatabaseHelper, unit_of_work: UnitOfWork
    ) -> AsyncGenerator[AsyncSession, None]:
        async with db_helper.session_factory() as session:
            unit_of_work.add(SQLAlchemyTransaction(session))
            yield session
