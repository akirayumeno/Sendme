from datetime import timedelta, datetime, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.settings import settings

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")
SECRET_KEY = settings.SECRET_KEY  # get from config
ALGORITHM = settings.ALGORITHM

"""Responsible for user authentication."""


def hash_password(password: str) -> str:
	return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
	"""Verify whether the original password and the hashed password match."""
	return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
	"""Create JWT Access Token"""
	expires_delta = timedelta(minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES)
	expire = datetime.now(timezone.utc) + expires_delta

	access_to_encode = {
		"exp":expire,
		"sub":str(user_id),
		"type":"access"
	}

	return encode_jwt(access_to_encode)


def create_refresh_token(user_id: int, jti: str) -> str:
	"""Create JWT Refresh Token"""
	expires_delta = timedelta(days = settings.REFRESH_TOKEN_EXPIRE_DAYS)
	expire_dt = expires_delta + datetime.now(timezone.utc)
	refresh_to_encode = {
		"exp":expire_dt,
		"sub":str(user_id),
		"type":"refresh",
		"jti":jti
	}

	return encode_jwt(refresh_to_encode)


def decode_token(token):
	"""Decode JWT Token"""
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms = ALGORITHM)
		return payload
	except JWTError as e:
		raise ValueError(f"Could not validate credentials: {str(e)}")


def encode_jwt(payload):
	"""Encode JWT"""
	try:
		token = jwt.encode(payload, SECRET_KEY, algorithm = ALGORITHM)
		return token
	except JWTError as e:
		raise ValueError(f"Could not encode JWT: {str(e)}")
