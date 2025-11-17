# src.auth.config
from datetime import timedelta

from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
	JWT_ALG: str
	JWT_SECRET: str
	JWT_EXP: int = 5  # 分钟

	REFRESH_TOKEN_KEY: str
	REFRESH_TOKEN_EXP: timedelta = timedelta(days = 30)

	SECURE_COOKIES: bool = True


auth_settings = AuthConfig()

# src.config
from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings

from src.constants import Environment


class Config(BaseSettings):
	DATABASE_URL: PostgresDsn
	REDIS_URL: RedisDsn

	SITE_DOMAIN: str = "myapp.com"

	ENVIRONMENT: Environment = Environment.PRODUCTION

	SENTRY_DSN: str | None = None

	CORS_ORIGINS: list[str]
	CORS_ORIGINS_REGEX: str | None = None
	CORS_HEADERS: list[str]

	APP_VERSION: str = "1.0"


settings = Config()
