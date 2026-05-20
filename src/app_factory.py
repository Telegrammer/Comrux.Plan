from contextlib import asynccontextmanager
import logging

from dishka import AsyncContainer, make_async_container
import dishka.integrations.fastapi as fastapi_integration
import dishka.integrations.faststream as faststream_integration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from faststream import ContextRepo, FastStream
from faststream.kafka import KafkaBroker
from redis.asyncio import Redis

from application.ports import ChatSessionSavePolicy
from infrastructure.subscribers.chat import chat_sub_router
from presentation.http.controllers import chat_http_router
from presentation.ws.controllers import chat_ws_router
from setup import DatabaseHelper, Settings, settings
from setup.providers import (
    ApplicationProvider,
    DatabaseProvider,
    DomainProvider,
    PresentationProvider,
    RuntimeProvider,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    broker = KafkaBroker(str(settings.transport.kafka_url).replace("kafka://", ""))
    container: AsyncContainer = make_async_container(
        DatabaseProvider(),
        DomainProvider(),
        ApplicationProvider(),
        RuntimeProvider(),
        PresentationProvider(),
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
            save_policy = await app_state.get(ChatSessionSavePolicy)
            await save_policy.start()
            await broker.start()
            try:
                yield
            finally:
                await broker.stop()
                await save_policy.stop()

        db_helper = await container.get(DatabaseHelper)
        redis = await container.get(Redis)
        await redis.aclose()
        await db_helper.dispose()

    app = FastAPI(title="Comrux.Chat", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(chat_http_router)
    app.include_router(chat_ws_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    fastapi_integration.setup_dishka(container=container, app=app)
    logger.info("Chat app created")
    return app
