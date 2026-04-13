from dataclasses import dataclass
from uuid import UUID

from application.ports.gateways import ActorCommandGateway, ActorQueryGateway
from domain.entities.actor import Actor, ActorId
from domain.services import ActorService


@dataclass(frozen=True)
class CreateActorRequest:
    actor_id: ActorId
    display_name: str
    public_id: str

    @classmethod
    def from_primitives(
        cls, actor_id: str, display_name: str, *, email: str
    ) -> "CreateActorRequest":
        return cls(
            actor_id=ActorId(UUID(actor_id)),
            display_name=display_name,
            public_id=email,
        )


@dataclass(frozen=True)
class CreateActorResponse:
    actor_id: ActorId
    was_created: bool

    @classmethod
    def from_entity(cls, actor: Actor, was_created: bool) -> "CreateActorResponse":
        return cls(actor_id=actor.id, was_created=was_created)


class CreateActorUsecase:
    def __init__(
        self,
        actor_queries: ActorQueryGateway,
        actor_commands: ActorCommandGateway,
        actor_service: ActorService,
    ) -> None:
        self._actor_queries = actor_queries
        self._actor_commands = actor_commands
        self._actor_service = actor_service

    async def __call__(self, request: CreateActorRequest) -> CreateActorResponse:
        existing_actor = await self._actor_queries.by_id(request.actor_id)
        if existing_actor is not None:
            return CreateActorResponse.from_entity(existing_actor, was_created=False)

        new_actor = self._actor_service.create_actor(
            actor_id=request.actor_id,
            display_name=request.display_name,
            public_id=request.public_id,
        )
        await self._actor_commands.add(new_actor)
        return CreateActorResponse.from_entity(new_actor, was_created=True)
