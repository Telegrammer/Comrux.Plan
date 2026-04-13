from dataclasses import dataclass
from enum import StrEnum


class ContextKind(StrEnum):
    PROJECT = "project"
    DOCUMENT = "document"


@dataclass(frozen=True)
class ContextRef:
    kind: ContextKind
    external_id: str
