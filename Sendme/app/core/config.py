from pydantic import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key"  # 生成：openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/sendme"

    class Config:
        case_sensitive = True

settings = Settings()