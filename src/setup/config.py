from pathlib import Path

from pydantic import BaseModel, KafkaDsn, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8009


class TransportConfig(BaseModel):
    kafka_url: KafkaDsn


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 10
    max_overflow: int = 10


class ServiceConfig(BaseModel):
    encryption_key: str


class RedisConfig(BaseModel):
    url: str = "redis://:chat@localhost:6382/0"


class AuthConfig(BaseModel):
    public_key_path: Path = BASE_DIR / "certificates" / "jwt-public.pem"
    algorithm: str = "RS256"


class ChatSessionConfig(BaseModel):
    history_limit: int = 50
    debounce_seconds: float = 5.0
    periodic_seconds: float = 30.0
    periodic_max_concurrency: int = 20


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env_app",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )

    run: RunConfig = RunConfig()
    db: DatabaseConfig
    transport: TransportConfig
    service: ServiceConfig
    redis: RedisConfig = RedisConfig()
    auth: AuthConfig = AuthConfig()
    chat_session: ChatSessionConfig = ChatSessionConfig()


settings = Settings()
