from abc import ABC, abstractmethod
from typing import Type

from .transaction import Transaction


class UnitOfWork(ABC):
    @abstractmethod
    def add(self, transaction: Transaction) -> None: ...

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork": ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: BaseException | None,
    ) -> None: ...
