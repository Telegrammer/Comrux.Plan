from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import InterfaceError, OperationalError

from application.exceptions import GatewayFailedError, InconsistentDataError

from .common import create_error_aware_decorator

network_error_aware = create_error_aware_decorator(
    {
        frozenset(
            {
                ConnectionRefusedError,
                ConnectionResetError,
                InterfaceError,
                OperationalError,
                RedisConnectionError,
            }
        ): GatewayFailedError
    }
)

stale_data_error_aware = create_error_aware_decorator({})
