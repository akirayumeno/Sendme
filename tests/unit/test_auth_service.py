from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.auth_service import AuthService


@pytest.fixture
def mock_repos():
	"""Create mocks for all repository dependencies."""
	return {
		"user_repo":AsyncMock(),
		"token_repo":AsyncMock(),
		"redis_repo":AsyncMock()
	}


@pytest.fixture
def auth_service(mock_repos):
	"""Inject mocks into AuthService."""
	return AuthService(
		user_repo = mock_repos["user_repo"],
		token_repo = mock_repos["token_repo"],
		redis_repo = mock_repos["redis_repo"]
	)


@pytest.mark.asyncio
class TestAuthService:

	# --- Register Tests ---

	async def test_register_success(self, auth_service, mock_repos):
		# Setup Mocks
		mock_repos["redis_repo"].get_otp.return_value = "123456"
		mock_repos["user_repo"].get_user_by_username.return_value = None

		# Mocking the new user object
		new_user = MagicMock()
		new_user.id = 1
		new_user.username = "testuser"
		mock_repos["user_repo"].create_user.return_value = new_user

		# Execute
		result = await auth_service.register_with_otp("testuser", "password123", "123456")

		# Verify
		assert result["username"] == "testuser"
		mock_repos["redis_repo"].delete_otp.assert_awaited_once_with("testuser")
		mock_repos["user_repo"].create_user.assert_awaited_once()

	async def test_register_invalid_otp(self, auth_service, mock_repos):
		# Setup: Redis has one code, but user provides another
		mock_repos["redis_repo"].get_otp.return_value = "111111"

		with pytest.raises(ValueError, match = "Invalid or expired verification code."):
			await auth_service.register_with_otp("testuser", "password", "wrong_otp")

	# --- Login Tests ---

	async def test_login_success(self, auth_service, mock_repos, monkeypatch):
		# Mocking security functions using monkeypatch
		monkeypatch.setattr("app.core.security.verify_password", lambda p, h:True)
		monkeypatch.setattr("app.core.security.create_access_token", lambda uid:"fake_access")
		monkeypatch.setattr("app.core.security.create_refresh_token", lambda uid, jti:"fake_refresh")

		# Setup User Mock
		user = MagicMock()
		user.id = 99
		user.hashed_password = "hashed_in_db"
		mock_repos["user_repo"].get_user_by_username.return_value = user

		# Execute
		result = await auth_service.login("testuser", "password123")

		# Verify
		assert result["access_token"] == "fake_access"
		assert result["refresh_token"] == "fake_refresh"
		# Ensure the refresh token was recorded in DB
		mock_repos["token_repo"].create_token_record.assert_awaited_once()

	# --- Refresh Token Tests ---

	async def test_refresh_token_success(self, auth_service, mock_repos, monkeypatch):
		# Mock security.decode_token to return valid payload
		fake_payload = {"type":"refresh", "sub":99, "jti":"some-uuid"}
		monkeypatch.setattr("app.core.security.decode_token", lambda t:fake_payload)
		monkeypatch.setattr("app.core.security.create_access_token", lambda uid:"new_access_token")

		# Mock DB finding an unused token
		mock_repos["token_repo"].get_unused_token.return_value = MagicMock()

		# Execute
		result = await auth_service.refresh_access_token("valid_refresh_token")

		# Verify
		assert result["access_token"] == "new_access_token"
		mock_repos["token_repo"].get_unused_token.assert_awaited_once_with("some-uuid")

	async def test_refresh_token_revoked(self, auth_service, mock_repos, monkeypatch):
		# Mock token is valid in format but revoked in DB
		monkeypatch.setattr("app.core.security.decode_token", lambda t:{"type":"refresh", "jti":"revoked-jti"})
		mock_repos["token_repo"].get_unused_token.return_value = None

		with pytest.raises(ValueError, match = "Refresh token has been revoked or used."):
			await auth_service.refresh_access_token("revoked_token")
