import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.core import security
from app.core.settings import settings
from app.services.exceptions import OtpInvalidError, OtpLockedError, RateLimitError
from app.services.notification_service import notification_service
from app.storage.abstract_metadata_repo import AbstractRefreshTokenRepository, AbstractUserRepository
from app.storage.exceptions import UserConstraintError
from app.storage.redis_repo import RedisRepo


class AuthService:
	def __init__(
			self,
			user_repo: AbstractUserRepository,
			token_repo: AbstractRefreshTokenRepository,
			redis_repo: RedisRepo,
	):
		self.user_repo = user_repo
		self.token_repo = token_repo
		self.redis_repo = redis_repo

	@staticmethod
	def _generate_otp() -> str:
		return f"{secrets.randbelow(1_000_000):06d}"

	async def request_register_otp(self, email: str, username: str, password: str) -> dict:
		"""
		Step 1: create/update an unverified user in DB, then send OTP to email.
		Only OTP state is kept in Redis.
		"""
		if await self.redis_repo.is_otp_locked(email):
			raise OtpLockedError("Too many failed attempts. Try again later.")
		if await self.redis_repo.has_otp_cooldown(email):
			raise RateLimitError("OTP sent too frequently. Please wait.")

		existing_by_email = await self.user_repo.get_user_by_email(email)
		existing_by_username = await self.user_repo.get_user_by_username(username)

		# Username cannot belong to another account.
		if existing_by_username and (not existing_by_email or existing_by_username.id != existing_by_email.id):
			raise UserConstraintError(f"Username {username} already exists.")

		# Verified email cannot register again.
		if existing_by_email and existing_by_email.is_verified:
			raise UserConstraintError(f"Email {email} already exists.")

		hashed_password = security.hash_password(password)

		if existing_by_email:
			await self.user_repo.update_user(
				existing_by_email.id,
				{
					"username":username,
					"hashed_password":hashed_password,
					"is_verified":False,
				},
			)
		else:
			await self.user_repo.create_user(
				username = username,
				hashed_password = hashed_password,
				email = email,
				is_verified = False,
			)

		otp = self._generate_otp()
		await self.redis_repo.set_otp(email, otp, ex = settings.OTP_EXPIRATION_SECONDS)
		await self.redis_repo.set_otp_cooldown(email, settings.OTP_RESEND_COOLDOWN_SECONDS)

		await notification_service.send_verification_mail(email, username, otp)
		return {"message":"Verification code sent."}

	async def register_with_otp(self, email: str, otp_code: str) -> dict:
		"""
		Step 2: verify OTP and mark DB user as verified.
		"""
		if await self.redis_repo.is_otp_locked(email):
			raise OtpLockedError("Too many failed attempts. Try again later.")

		saved_otp = await self.redis_repo.get_otp(email)
		if not saved_otp or saved_otp != otp_code:
			attempts = await self.redis_repo.incr_otp_attempts(email, ex = settings.OTP_EXPIRATION_SECONDS)
			if attempts >= settings.OTP_MAX_ATTEMPTS:
				await self.redis_repo.lock_otp(email, ex = settings.OTP_LOCK_SECONDS)
			raise OtpInvalidError("Invalid or expired verification code.")

		user = await self.user_repo.get_user_by_email(email)
		if not user:
			raise OtpInvalidError("No pending registration for this email.")
		if user.is_verified:
			return {"id":user.id, "username":user.username, "email":user.email}

		updated_user = await self.user_repo.update_user(user.id, {"is_verified":True})
		await self.redis_repo.clear_otp_state(email)
		await self.redis_repo.clear_otp_attempts(email)

		return {"id":updated_user.id, "username":updated_user.username, "email":updated_user.email}

	async def login(self, username: str, password: str) -> dict:
		"""
		Authenticate user and issue dual JWT tokens (Access + Refresh).
		"""
		user = await self.user_repo.get_user_by_username(username)
		if not user or not security.verify_password(password, user.hashed_password):
			raise ValueError("Invalid username or password.")
		if not user.is_verified:
			raise ValueError("Email not verified.")

		refresh_jti = str(uuid.uuid4())
		access_token = security.create_access_token(user.id)
		refresh_token = security.create_refresh_token(user.id, refresh_jti)

		expires_at = datetime.now(timezone.utc) + timedelta(days = settings.REFRESH_TOKEN_EXPIRE_DAYS)
		await self.token_repo.create_token_record(
			user_id = user.id,
			token_jti = refresh_jti,
			expires_at = expires_at,
		)

		return {
			"access_token":access_token,
			"refresh_token":refresh_token,
			"token_type":"bearer",
		}

	async def refresh_access_token(self, refresh_token: str) -> dict:
		payload = security.decode_token(refresh_token)
		if payload.get("type") != "refresh":
			raise ValueError("Invalid token type.")

		user_id = payload.get("sub")
		jti = payload.get("jti")
		db_token = await self.token_repo.get_unused_token(jti)
		if not db_token:
			raise ValueError("Refresh token has been revoked or used.")
		if user_id is None:
			raise ValueError("Invalid refresh token payload.")

		new_access_token = security.create_access_token(int(user_id))
		return {"access_token":new_access_token, "token_type":"bearer"}
