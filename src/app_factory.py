from contextlib import asynccontextmanager
import logging

from dishka import AsyncContainer, make_async_container
import dishka.integrations.fastapi as fastapi_integration
import dishka.integrations.faststream as faststream_integration
from fastapi import FastAPI
from faststream import ContextRepo, FastStream
from faststream.kafka import KafkaBroker

from infrastructure.subscribers.chat import chat_sub_router
from setup import (
    ApplicationProvider,
    DatabaseHelper,
    DatabaseProvider,
    DomainProvider,
    Settings,
    settings,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    broker = KafkaBroker(str(settings.transport.kafka_url).replace("kafka://", ""))
    container: AsyncContainer = make_async_container(
        DatabaseProvider(),
        DomainProvider(),
        ApplicationProvider(),
        context={Settings: settings, KafkaBroker: broker},
    )

    broker.include_router(chat_sub_router)
    faststream_integration.setup_dishka(
        container=container,
        app=FastStream(broker, context=ContextRepo()),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with container() as app_state:
            app.state.container = app_state
            await broker.start()
            try:
                yield
            finally:
                await broker.stop()

        db_helper = await container.get(DatabaseHelper)
        await db_helper.dispose()

    app = FastAPI(title="Comrux.Chat", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    fastapi_integration.setup_dishka(container=container, app=app)
    logger.info("Chat app created")
    return app
