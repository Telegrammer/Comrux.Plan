from application.ports import ChatSessionSavePolicy
from domain.entities.chat import ChatId


class CompositeChatSessionSavePolicy(ChatSessionSavePolicy):
    def __init__(self, policies: list[ChatSessionSavePolicy]) -> None:
        self._policies = policies

    async def start(self) -> None:
        for policy in self._policies:
            await policy.start()

    async def stop(self) -> None:
        for policy in self._policies:
            await policy.stop()

    async def on_room_modified(self, chat_id: ChatId) -> None:
        for policy in self._policies:
            await policy.on_room_modified(chat_id)

    async def on_room_closed(self, chat_id: ChatId) -> None:
        for policy in self._policies:
            await policy.on_room_closed(chat_id)
