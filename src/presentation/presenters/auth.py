from dataclasses import dataclass
from typing import Any

import jwt

from presentation.exceptions import ExpiredAccessTokenError, InvalidAccessTokenError


@dataclass(frozen=True)
class AccessAuthInfo:
    key_id: str
    user_id: str


class JwtAccessTokenPresenter:
    def __init__(self, public_key: str, algorithm: str) -> None:
        self._public_key = public_key
        self._algorithm = algorithm

    def present(self, token: str) -> AccessAuthInfo:
        try:
            payload: dict[str, Any] = jwt.decode(
                jwt=token,
                key=self._public_key,
                algorithms=[self._algorithm],
            )
        except jwt.exceptions.ExpiredSignatureError as error:
            raise ExpiredAccessTokenError("Given access token is expired") from error
        except jwt.exceptions.PyJWTError as error:
            raise InvalidAccessTokenError("Invalid access token") from error

        if payload.get("type") != "access":
            raise InvalidAccessTokenError("Token is not access")

        user_id = payload.get("user_id")
        if not isinstance(user_id, str):
            raise InvalidAccessTokenError("Token does not contain user_id")

        key_id = payload.get("sub")
        if not isinstance(key_id, str):
            raise InvalidAccessTokenError("Token does not contain key id")

        return AccessAuthInfo(key_id=key_id, user_id=user_id)
