from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette import status

from app.core.database import get_db
from app.core.exceptions import CREDENTIALS_EXCEPTION
from app.core.orm_models import User
from app.storage.abstract_metadata_repo import AbstractUserRepository, AbstractMessageRepository, \
	AbstractCapacityRepository
from app.storage.exceptions import UserNotFoundError
from app.storage.sqlalchemy_repo import UserRepository, MessageRepository, CapacityRepository


# Inject Session and instantiate repository
def get_user_repository(db: Session = Depends(get_db)) -> AbstractUserRepository:
	return UserRepository(db)


def get_message_repository(db: Session = Depends(get_db)) -> AbstractMessageRepository:
	return MessageRepository(db)


def get_capacity_repository(db: Session = Depends(get_db)) -> AbstractCapacityRepository:
	return CapacityRepository(db)


def jwt_verify(
		token: str = Depends(OAuth2PasswordBearer(tokenUrl = "/auth/token")),
) -> int:
	try:
		payload = jwt.decode(token, "JWT_SECRET", algorithms = ["HS256"])
		user_id: str | None = payload.get("sub")

		if not user_id:
			raise CREDENTIALS_EXCEPTION
		return int(user_id)
	except (JWTError, ValueError):
		raise CREDENTIALS_EXCEPTION


def get_current_user(
		user_id: int = Depends(jwt_verify),
		user_repo: AbstractUserRepository = Depends(get_user_repository)
) -> User:
	try:
		user = user_repo.get_user_by_id(user_id)
		return user
	except UserNotFoundError:
		raise CREDENTIALS_EXCEPTION from None


def get_current_active_user(user: User = Depends(get_current_user)):
	if not user.is_verified:
		raise HTTPException(
			status.HTTP_403_FORBIDDEN,
			detail = "Please verify your email first."
		)
	return user


def check_user_capacity(
		file_size: int,
		current_user: User = Depends(get_current_active_user),
		capacity_repo: AbstractCapacityRepository = Depends(get_capacity_repository)
):
	"""Check the total file size of the current user and the size of the currently uploaded file."""
	# Check the total file size of the current user
	user_id = current_user.id
	used_capacity = capacity_repo.get_used_capacity(user_id)
	total_capacity = capacity_repo.get_capacity_by_user_id(user_id)

	# Check if the total capacity is exceeded.
	if used_capacity + file_size > total_capacity:
		raise HTTPException(
			status_code = status.HTTP_403_FORBIDDEN,
			detail = "Upload failed: Storage capacity is full. Please delete some messages or upgrade your account."
		)
	return True
