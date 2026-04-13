from abc import ABC, abstractmethod


class Transaction(ABC):
    @abstractmethod
    async def complete(self) -> None: ...

    @abstractmethod
    async def cancel(self) -> None: ...
