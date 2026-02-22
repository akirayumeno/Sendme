import uuid

from app.core import security


def test_password_hashing_logic():
	raw_password = "my_super_secret"
	hashed = security.hash_password(raw_password)

	assert hashed != raw_password

	assert security.verify_password(raw_password, hashed) is True
	assert security.verify_password("wrong_password", hashed) is False


def test_create_access_token():
	user_id = 12345
	result = security.create_access_token(user_id)
	assert result is not None


def test_create_refresh_token():
	user_id = 12345
	jti = str(uuid.uuid4())
	result = security.create_refresh_token(user_id, jti)
	assert result is not None
