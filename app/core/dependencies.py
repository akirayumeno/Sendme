from pathlib import Path

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import CREDENTIALS_EXCEPTION
from app.core.orm_models import User
from app.core.settings import settings
from app.services.auth_service import AuthService
from app.services.file_service import FileService
from app.services.message_service import MessageService
from app.storage.exceptions import UserNotFoundErrorById
from app.storage.file_repo import FileRepo
from app.storage.redis_repo import RedisRepo
from app.storage.sqlalchemy_repo import MessageRepository, RefreshTokenRepository, UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/api/v1/auth/login")


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
	return UserRepository(db)


def get_message_repository(db: AsyncSession = Depends(get_db)) -> MessageRepository:
	return MessageRepository(db)


def get_refresh_token_repository(db: AsyncSession = Depends(get_db)) -> RefreshTokenRepository:
	return RefreshTokenRepository(db)


def get_redis_repo() -> RedisRepo:
	return RedisRepo(settings.REDIS_URL)


def get_file_repo() -> FileRepo:
	return FileRepo(upload_dir = Path(settings.UPLOAD_DIR))


def get_auth_service(
		user_repo: UserRepository = Depends(get_user_repository),
		token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
		redis_repo: RedisRepo = Depends(get_redis_repo),
) -> AuthService:
	return AuthService(user_repo = user_repo, token_repo = token_repo, redis_repo = redis_repo)


def get_file_service(
		file_repo: FileRepo = Depends(get_file_repo),
		message_repo: MessageRepository = Depends(get_message_repository),
		user_repo: UserRepository = Depends(get_user_repository),
		redis_repo: RedisRepo = Depends(get_redis_repo),
) -> FileService:
	return FileService(file_repo = file_repo, message_repo = message_repo, user_repo = user_repo, redis_repo = redis_repo)


def get_message_service(
		message_repo: MessageRepository = Depends(get_message_repository),
		user_repo: UserRepository = Depends(get_user_repository),
		file_service: FileService = Depends(get_file_service),
		redis_repo: RedisRepo = Depends(get_redis_repo),
) -> MessageService:
	return MessageService(
		message_repo = message_repo,
		user_repo = user_repo,
		file_service = file_service,
		redis_repo = redis_repo,
	)


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
	try:
		payload = jwt.decode(token, settings.SECRET_KEY, algorithms = [settings.ALGORITHM])
		if payload.get("type") != "access":
			raise CREDENTIALS_EXCEPTION
		user_id = payload.get("sub")
		if user_id is None:
			raise CREDENTIALS_EXCEPTION
		return int(user_id)
	except (JWTError, ValueError, TypeError):
		raise CREDENTIALS_EXCEPTION


async def get_current_user(
		user_id: int = Depends(get_current_user_id),
		user_repo: UserRepository = Depends(get_user_repository),
) -> User:
	try:
		return await user_repo.get_user_by_id(user_id)
	except UserNotFoundErrorById:
		raise CREDENTIALS_EXCEPTION from None
