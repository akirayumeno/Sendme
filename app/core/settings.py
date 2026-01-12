# src.auth.config
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	DATABASE_URL: str = Field(
		default = "postgresql://user:password@localhost:5432/local_db",
		description = "Database connection string"
	)
	# --- JWT ---
	SECRET_KEY: str = Field(
		default = "dangerous-default-key-replace-me-in-env",
		description = "The key used for JWT signing must be a strongly random value in a production environment."
	)
	ALGORITHM: str = "HS256"

	# --- Token validity period configuration (unit: minutes or days) ---
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
	REFRESH_TOKEN_EXPIRE_DAYS: int = 7

	# --- Service Capacity Configuration ---
	# Define the default maximum capacity limit (1G)
	DEFAULT_MAX_CAPACITY_BYTES: int = 1024 * 1024 * 1024

	# Pydantic V2 Configuration
	model_config = SettingsConfigDict(
		env_file = '.env',
		extra = 'ignore'
	)


settings = Settings()
