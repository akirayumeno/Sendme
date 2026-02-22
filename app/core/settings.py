# src.auth.config
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	DATABASE_URL: str = Field(
		default = "postgresql://user:password@localhost:5432/local_db",
		description = "Database connection string"
	)

	# --- SMTP ---
	SMTP_SERVER: str = Field(default = "smtp.gmail.com", description = "SMTP server host")
	SMTP_PORT: int = Field(default = 587, description = "SMTP server port")
	SMTP_EMAIL: str = Field(default = "your-email@gmail.com", description = "Sender email address")
	SMTP_CODE: str = Field(default = "", description = "SMTP app password/auth code")

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

	# --- Message DELETE TTL ---
	MESSAGE_TTL_SECONDS: int = 86400

	# Pydantic V2 Configuration
	model_config = SettingsConfigDict(
		env_file = '.env',
		extra = 'ignore'
	)


settings = Settings()
