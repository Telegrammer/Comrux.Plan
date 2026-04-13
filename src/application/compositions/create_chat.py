import logging

from application.ports import UnitOfWork
from application.usecases import (
    CreateChatRequest,
    CreateChatResponse,
    CreateChatUsecase,
    CreateSystemMessageRequest,
    CreateSystemMessageUsecase,
)

logger = logging.getLogger(__name__)

SYSTEM_CHAT_CREATED_MESSAGE = "Chat created"


class CreateChatComposition:
    def __init__(
        self,
        create_chat: CreateChatUsecase,
        create_system_message: CreateSystemMessageUsecase,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._create_chat = create_chat
        self._create_system_message = create_system_message
        self._unit_of_work = unit_of_work

    async def __call__(self, request: CreateChatRequest) -> CreateChatResponse:
        logger.info(
            "Chat creation started for %s:%s",
            request.context.kind.value,
            request.context.external_id,
        )

        async with self._unit_of_work:
            response = await self._create_chat(request)
            if response.was_created:
                await self._create_system_message(
                    CreateSystemMessageRequest(
                        chat_id=response.chat_id,
                        content=SYSTEM_CHAT_CREATED_MESSAGE,
                    )
                )

        if response.was_created:
            logger.info("Chat %s created successfully", response.chat_id.value)
        else:
            logger.info(
                "Chat for %s:%s already exists",
                request.context.kind.value,
                request.context.external_id,
            )
        return response
