# src.auth.config
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	DATABASE_URL: str = Field(
		default = "postgresql+asyncpg://user:password@localhost:5432/local_db",
		description = "Database connection string"
	)
	REDIS_URL: str = Field(default = "redis://localhost:6379", description = "Redis connection URL")
	UPLOAD_DIR: str = Field(default = "uploads", description = "Local upload directory")

	# --- SMTP ---
	RESEND_API_KEY: str = "re_your_default_key_for_test"  # 或者不给默认值，强制要求环境变量
	RESEND_FROM_EMAIL: str = "onboarding@send-me.dev"
	
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

	# --- Auth (OTP) ---
	OTP_EXPIRATION_SECONDS: int = 300
	OTP_RESEND_COOLDOWN_SECONDS: int = 60
	OTP_MAX_ATTEMPTS: int = 5
	OTP_LOCK_SECONDS: int = 600

	# --- Message DELETE TTL ---
	MESSAGE_TTL_SECONDS: int = 86400

	# Pydantic V2 Configuration
	model_config = SettingsConfigDict(
		env_file = '.env',
		extra = 'ignore'
	)


settings = Settings()
