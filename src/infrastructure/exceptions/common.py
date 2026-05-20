import functools
import inspect
import logging
from collections.abc import Callable

from application.exceptions import ApplicationError

logger = logging.getLogger(__name__)

type ErrorFactory = Callable[[Exception], ApplicationError]


def error_aware(
    error_map: dict[type[BaseException] | frozenset[type[BaseException]], ErrorFactory],
):
    flattened_error_map: dict[type[BaseException], ErrorFactory] = {}
    for raw, factory in error_map.items():
        if isinstance(raw, frozenset):
            for error_type in raw:
                flattened_error_map[error_type] = factory
        else:
            flattened_error_map[raw] = factory

    def decorator[T, **P](func: Callable[P, T]) -> Callable[P, T]:
        def handle_error(unknown: Exception) -> None:
            target_name = func.__qualname__
            factory = flattened_error_map.get(type(unknown))
            if factory is None:
                raise

            application_error = factory(unknown)
            logger.error(
                "Infrastructure exception '%s' caught in '%s'. Converting to '%s'.",
                type(unknown).__name__,
                target_name,
                type(application_error).__name__,
            )
            raise application_error from unknown

        @functools.wraps(func)
        def sync_handler(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                handle_error(exc)

        @functools.wraps(func)
        async def async_handler(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                handle_error(exc)

        return async_handler if inspect.iscoroutinefunction(func) else sync_handler

    return decorator


def create_error_aware_decorator(
    base_error_map: dict[
        type[Exception] | frozenset[type[Exception]],
        type[ApplicationError],
    ],
):
    def outer(default_message: str | None = None):
        def decorator(func=None, *, error_map=None):
            final_map = base_error_map.copy()
            if error_map:
                final_map.update(error_map)

            factory_map = {
                key: (
                    (lambda error_cls: (lambda error: error_cls(str(error))))(value)
                    if default_message is None
                    else (lambda error_cls: (lambda _: error_cls(default_message)))(value)
                )
                for key, value in final_map.items()
            }

            return error_aware(factory_map)(func) if func else error_aware(factory_map)

        return decorator

    return outer
