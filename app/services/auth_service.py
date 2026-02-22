import uuid
from datetime import datetime, timezone, timedelta

from app.core import security
from app.core.settings import settings
from app.storage.abstract_metadata_repo import AbstractUserRepository, AbstractRefreshTokenRepository
from app.storage.exceptions import UserConstraintError
from app.storage.redis_repo import RedisRepo


class AuthService:
	def __init__(
			self,
			user_repo: AbstractUserRepository,
			token_repo: AbstractRefreshTokenRepository,
			redis_repo: RedisRepo
	):
		self.user_repo = user_repo
		self.token_repo = token_repo
		self.redis_repo = redis_repo

	async def register_with_otp(self, username: str, password: str, otp_code: str) -> dict:
		"""
		Register a new user after verifying the OTP code from Redis.
		"""
		# 1. Verify Dynamic CAPTCHA from Redis
		saved_otp = await self.redis_repo.get_otp(username)
		if not saved_otp or saved_otp != otp_code:
			raise ValueError("Invalid or expired verification code.")

		# 2. Check if user already exists
		existing_user = await self.user_repo.get_user_by_username(username)
		if existing_user:
			raise UserConstraintError(f"User {username} already exists.")

		# 3. Hash password and create user
		hashed_password = security.hash_password(password)
		new_user = await self.user_repo.create_user(username, hashed_password)

		# 4. Cleanup OTP after successful registration
		await self.redis_repo.delete_otp(username)

		return {"id":new_user.id, "username":new_user.username}

	async def login(self, username: str, password: str) -> dict:
		"""
		Authenticate user and issue dual JWT tokens (Access & Refresh).
		"""
		# 1. Validate credentials
		user = await self.user_repo.get_user_by_username(username)
		if not user or not security.verify_password(password, user.hashed_password):
			raise ValueError("Invalid username or password.")

		# 2. Generate unique JTI for the Refresh Token to allow revocation
		refresh_jti = str(uuid.uuid4())

		# 3. Create Tokens
		access_token = security.create_access_token(user.id)
		refresh_token = security.create_refresh_token(user.id, refresh_jti)

		# 4. Store Refresh Token record in Postgres for session management
		# This allows us to revoke specific sessions later.
		expires_at = datetime.now(timezone.utc) + timedelta(days = settings.REFRESH_TOKEN_EXPIRE_DAYS)
		await self.token_repo.create_token_record(
			user_id = user.id,
			token_jti = refresh_jti,
			expires_at = expires_at
		)

		return {
			"access_token":access_token,
			"refresh_token":refresh_token,
			"token_type":"bearer"
		}

	async def refresh_access_token(self, refresh_token: str) -> dict:
		"""
		Use a valid Refresh Token to issue a new Access Token.
		"""
		# 1. Decode and validate the Refresh Token
		payload = security.decode_token(refresh_token)  # You'll need to add this to security.py
		if payload.get("type") != "refresh":
			raise ValueError("Invalid token type.")

		user_id = payload.get("sub")
		jti = payload.get("jti")

		# 2. Check if JTI exists and is not used in DB
		db_token = await self.token_repo.get_unused_token(jti)
		if not db_token:
			raise ValueError("Refresh token has been revoked or used.")

		# 3. Issue new Access Token
		new_access_token = security.create_access_token(user_id)
		return {"access_token":new_access_token, "token_type":"bearer"}
