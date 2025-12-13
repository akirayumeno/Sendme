import uuid
from datetime import timedelta, datetime, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.orm_models import User
from app.core.settings import Settings
from app.services.exceptions import ServiceError, UserAuthenticationError
from app.storage.exceptions import UserConstraintError, RepositoryError
from app.storage.sqlalchemy_repo import UserRepository, RefreshTokenRepository

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")
SECRET_KEY = Settings.SECRET_KEY  # get from config
ALGORITHM = "HS256"


class AuthService:
	"""Responsible for handling business logic related to user authentication."""

	def __init__(self, user_repo: UserRepository, refresh_token_repo: RefreshTokenRepository):
		"""inject UserRepository instance"""
		self.user_repo = user_repo
		self.refresh_token_repo = refresh_token_repo

	def verify_password(self, plain_password: str, hashed_password: str) -> bool:
		"""Verify whether the original password and the hashed password match."""
		return pwd_context.verify(plain_password, hashed_password)

	def create_access_token(self, user_id: int, expires_delta: Optional[timedelta] = None):
		"""Create JWT Access Token"""
		expires_delta = expires_delta or timedelta(minutes = Settings.ACCESS_TOKEN_EXPIRE_MINUTES)
		expire = datetime.now(timezone.utc) + expires_delta

		to_encode = {
			"exp":expire,
			"sub":str(user_id),
			"type":"access"
		}

		return jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)

	def create_refresh_token(self, user_id: int):
		"""Create JWT Refresh Token"""
		expires_delta = timedelta(days = Settings.REFRESH_TOKEN_EXPIRE_DAYS)
		expire_dt = expires_delta + datetime.now(timezone.utc)
		jti = str(uuid.uuid4())

		to_encode = {
			"exp":expire_dt,
			"sub":str(user_id),
			"jti":jti,
			"type":"refresh",
		}
		refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)

		try:
			self.refresh_token_repo.create_token_record(
				user_id = user_id,
				token_jti = jti,
				expires_at = expire_dt,
			)
		except RepositoryError as e:
			raise ServiceError("System error during refresh token creation.") from e
		return refresh_token

	def register_user(self, username: str, password: str) -> User:
		"""Process user registration transactions, including password hashing and creating database records."""
		hashed_password = pwd_context.hash(password)

		try:
			new_user = self.user_repo.create_user(
				username = username,
				hashed_password = hashed_password
			)

			return new_user

		except UserConstraintError as e:
			raise e

		except RepositoryError as e:
			raise ServiceError(f"Underlying service error: Could not complete registration.") from e

	def login_user(self, username: str, password: str) -> tuple[str, str]:
		"""Handle user login transactions: locate the user, verify the password, and generate an Access Token."""
		user = self.user_repo.get_user_by_username(username)
		if not user or not self.verify_password(password, user.hashed_password):
			raise UserAuthenticationError

		access_token = self.create_access_token(user_id = user.id)
		refresh_token = self.create_refresh_token(user_id = user.id)
		return access_token, refresh_token

	def refresh_access_token(self, refresh_token: str) -> str:
		"""Use a Refresh Token to exchange for a new Access Token."""
		try:
			# 1. Decode and verify the signature and format of the Refresh Token.
			payload = jwt.decode(refresh_token, SECRET_KEY, algorithms = [ALGORITHM])
			jti: str | None = payload.get("jti")
			user_id: str | None = payload.get("sub")

			if payload.get("type") != "refresh" or not jti or not user_id:
				raise UserAuthenticationError("Refresh token is invalid, expired, or revoked.")

			# 2. Check database records: Verify that the JTI exists, has expired, and has been used.

			token_record = self.refresh_token_repo.get_unused_token(jti)
			if not token_record:
				# Token does not exist, has expired, or has already been used.
				raise UserAuthenticationError("Refresh token is invalid, expired, or revoked.")

			# 3. Revoke the old token and create a new Access Token
			self.refresh_token_repo.mark_token_as_used(jti)

			# 4. Generate a new Access Token
			new_access_token = self.create_access_token(user_id = token_record.user_id)

			return new_access_token
		except JWTError as e:
			raise UserAuthenticationError(f"Invalid refresh token signature or structure.")
		except RepositoryError as e:
			raise ServiceError("System error during token refresh.") from e

	def logout_user(self, refresh_token_jti: str) -> bool:
		"""Logout a user's access token."""
		try:
			return self.refresh_token_repo.delete_token_record(refresh_token_jti)
		except RepositoryError as e:
			raise ServiceError("System error during logout (revoking token).") from e
