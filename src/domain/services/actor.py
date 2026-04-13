from domain.entities.actor import Actor, ActorId
from domain.value_objects import Name


class ActorService:
    def create_actor(
        self, actor_id: ActorId, display_name: str, public_id: str
    ) -> Actor:
        return Actor(
            id=actor_id,
            display_name=Name(display_name),
            public_id=public_id,
        )
