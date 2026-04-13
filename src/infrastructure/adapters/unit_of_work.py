from typing import Type

from application.ports import Transaction, UnitOfWork


class UnitOfWorkImpl(UnitOfWork):
    def __init__(self) -> None:
        self._transactions: list[Transaction] = []

    def add(self, transaction: Transaction) -> None:
        self._transactions.append(transaction)

    async def _complete(self) -> None:
        for transaction in self._transactions:
            await transaction.complete()

    async def _cancel(self) -> None:
        for transaction in self._transactions:
            await transaction.cancel()

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: BaseException | None,
    ) -> None:
        if exc_type is None:
            try:
                await self._complete()
            except Exception:
                await self._cancel()
                raise
        else:
            await self._cancel()

        self._transactions.clear()
