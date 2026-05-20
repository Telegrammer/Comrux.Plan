from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
import pytest

from presentation.exceptions import ExpiredAccessTokenError, InvalidAccessTokenError
from presentation.presenters import JwtAccessTokenPresenter


def build_keys() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def build_token(
    private_key: str,
    *,
    token_type: str = "access",
    expires_at: datetime | None = None,
) -> str:
    now = datetime.now(tz=UTC)
    return jwt.encode(
        {
            "sub": "key-1",
            "user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "iat": now.timestamp(),
            "exp": (expires_at or (now + timedelta(minutes=5))).timestamp(),
            "type": token_type,
        },
        private_key,
        algorithm="RS256",
    )


def test_jwt_access_token_presenter_decodes_valid_access_token() -> None:
    private_key, public_key = build_keys()
    presenter = JwtAccessTokenPresenter(public_key=public_key, algorithm="RS256")

    auth_info = presenter.present(build_token(private_key))

    assert auth_info.key_id == "key-1"
    assert auth_info.user_id == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_jwt_access_token_presenter_rejects_non_access_token() -> None:
    private_key, public_key = build_keys()
    presenter = JwtAccessTokenPresenter(public_key=public_key, algorithm="RS256")

    with pytest.raises(InvalidAccessTokenError):
        presenter.present(build_token(private_key, token_type="refresh"))


def test_jwt_access_token_presenter_rejects_expired_token() -> None:
    private_key, public_key = build_keys()
    presenter = JwtAccessTokenPresenter(public_key=public_key, algorithm="RS256")

    with pytest.raises(ExpiredAccessTokenError):
        presenter.present(
            build_token(
                private_key,
                expires_at=datetime.now(tz=UTC) - timedelta(minutes=1),
            )
        )
