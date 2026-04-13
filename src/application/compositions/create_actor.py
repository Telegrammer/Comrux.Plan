import logging

from application.ports import UnitOfWork
from application.usecases import CreateActorRequest, CreateActorResponse, CreateActorUsecase

logger = logging.getLogger(__name__)


class CreateActorComposition:
    def __init__(self, usecase: CreateActorUsecase, unit_of_work: UnitOfWork) -> None:
        self._usecase = usecase
        self._unit_of_work = unit_of_work

    async def __call__(self, request: CreateActorRequest) -> CreateActorResponse:
        logger.info("Actor creation started for %s", request.actor_id.value)
        async with self._unit_of_work:
            response = await self._usecase(request)
        if response.was_created:
            logger.info("Actor %s created", response.actor_id.value)
        else:
            logger.info("Actor %s already exists", response.actor_id.value)
        return response
