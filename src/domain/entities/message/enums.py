from enum import StrEnum


class MessageAuthorKind(StrEnum):
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"
