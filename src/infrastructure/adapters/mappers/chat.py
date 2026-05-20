from dataclasses import dataclass
from domain.entities.actor import ActorId
from domain.entities.chat import Chat, ChatMembership, ContextKind, ContextRef, ChatId
from application.ports.mappers import ChatMapper
from infrastructure.models import (
    Chat as ChatModel,
    ChatMembership as ChatMembershipModel,
)
from utils import ensure_utc_datetime


@dataclass
class ChatDTO:
    chat_model: ChatModel
    memberships: list[ChatMembershipModel]


class SQLAlchemyChatMapper(ChatMapper[ChatDTO]):
    def to_dto(self, domain: Chat) -> ChatDTO:
        return ChatDTO(
            chat_model=ChatModel(
                id=domain.id.value,
                name=domain.name,
                context_kind=domain.context.kind.value,
                context_external_id=domain.context.external_id,
                created_at=ensure_utc_datetime(domain.created_at),
                updated_at=ensure_utc_datetime(domain.updated_at),
            ),
            memberships=[
                ChatMembershipModel(
                    chat_id=member.chat.value,
                    actor_id=member.actor.value,
                    joined_at=ensure_utc_datetime(member.joined_at),
                )
                for member in domain.members
            ],
        )

    def to_domain(self, dto: ChatDTO) -> Chat:
        return Chat(
            id=ChatId(dto.chat_model.id),
            name=dto.chat_model.name,
            context=ContextRef(
                kind=ContextKind(dto.chat_model.context_kind),
                external_id=dto.chat_model.context_external_id,
            ),
            created_at=ensure_utc_datetime(dto.chat_model.created_at),
            updated_at=ensure_utc_datetime(dto.chat_model.updated_at),
            members=[
                ChatMembership(
                    chat=ChatId(member.chat_id),
                    actor=ActorId(member.actor_id),
                    joined_at=ensure_utc_datetime(member.joined_at),
                )
                for member in dto.memberships
            ],
        )
