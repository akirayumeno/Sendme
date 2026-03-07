from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.auth_service import AuthService
from app.services.exceptions import OtpInvalidError, OtpLockedError, RateLimitError


@pytest.fixture
def mock_repos():
	return {
		"user_repo": AsyncMock(),
		"token_repo": AsyncMock(),
		"redis_repo": AsyncMock(),
	}


@pytest.fixture
def auth_service(mock_repos):
	return AuthService(
		user_repo = mock_repos["user_repo"],
		token_repo = mock_repos["token_repo"],
		redis_repo = mock_repos["redis_repo"],
	)


@pytest.mark.asyncio
class TestAuthService:
	async def test_request_otp_success_create_user(self, auth_service, mock_repos, monkeypatch):
		mock_repos["redis_repo"].is_otp_locked.return_value = False
		mock_repos["redis_repo"].has_otp_cooldown.return_value = False
		mock_repos["user_repo"].get_user_by_email.return_value = None
		mock_repos["user_repo"].get_user_by_username.return_value = None

		monkeypatch.setattr("app.core.security.hash_password", lambda _pw: "hashed")
		mock_send = AsyncMock()
		monkeypatch.setattr("app.services.auth_service.notification_service.send_verification_mail", mock_send)
		monkeypatch.setattr(auth_service, "_generate_otp", lambda: "123456")

		result = await auth_service.request_register_otp("user@test.com", "testuser", "password123")

		assert result["message"] == "Verification code sent."
		mock_repos["user_repo"].create_user.assert_awaited_once_with(
			username = "testuser",
			hashed_password = "hashed",
			email = "user@test.com",
			is_verified = False,
		)
		mock_repos["redis_repo"].set_otp.assert_awaited_once()
		mock_send.assert_awaited_once_with("user@test.com", "testuser", "123456")

	async def test_request_otp_rate_limited(self, auth_service, mock_repos):
		mock_repos["redis_repo"].is_otp_locked.return_value = False
		mock_repos["redis_repo"].has_otp_cooldown.return_value = True

		with pytest.raises(RateLimitError):
			await auth_service.request_register_otp("user@test.com", "testuser", "password123")

	async def test_request_otp_locked(self, auth_service, mock_repos):
		mock_repos["redis_repo"].is_otp_locked.return_value = True
		with pytest.raises(OtpLockedError):
			await auth_service.request_register_otp("user@test.com", "testuser", "password123")

	async def test_register_with_otp_success(self, auth_service, mock_repos):
		mock_repos["redis_repo"].is_otp_locked.return_value = False
		mock_repos["redis_repo"].get_otp.return_value = "123456"

		user = MagicMock()
		user.id = 1
		user.username = "testuser"
		user.email = "user@test.com"
		user.is_verified = False
		mock_repos["user_repo"].get_user_by_email.return_value = user
		mock_repos["user_repo"].update_user.return_value = user

		result = await auth_service.register_with_otp("user@test.com", "123456")

		assert result["username"] == "testuser"
		mock_repos["user_repo"].update_user.assert_awaited_once_with(user.id, {"is_verified": True})
		mock_repos["redis_repo"].clear_otp_state.assert_awaited_once_with("user@test.com")

	async def test_register_with_otp_invalid(self, auth_service, mock_repos):
		mock_repos["redis_repo"].is_otp_locked.return_value = False
		mock_repos["redis_repo"].get_otp.return_value = "111111"
		mock_repos["redis_repo"].incr_otp_attempts.return_value = 1

		with pytest.raises(OtpInvalidError):
			await auth_service.register_with_otp("user@test.com", "000000")

	async def test_login_success(self, auth_service, mock_repos, monkeypatch):
		monkeypatch.setattr("app.core.security.verify_password", lambda _p, _h: True)
		monkeypatch.setattr("app.core.security.create_access_token", lambda _uid: "fake_access")
		monkeypatch.setattr("app.core.security.create_refresh_token", lambda _uid, _jti: "fake_refresh")

		user = MagicMock()
		user.id = 99
		user.hashed_password = "hashed_in_db"
		user.is_verified = True
		mock_repos["user_repo"].get_user_by_username.return_value = user

		result = await auth_service.login("testuser", "password123")

		assert result["access_token"] == "fake_access"
		assert result["refresh_token"] == "fake_refresh"
		mock_repos["token_repo"].create_token_record.assert_awaited_once()

	async def test_refresh_token_success(self, auth_service, mock_repos, monkeypatch):
		fake_payload = {"type": "refresh", "sub": "99", "jti": "some-uuid"}
		monkeypatch.setattr("app.core.security.decode_token", lambda _t: fake_payload)
		monkeypatch.setattr("app.core.security.create_access_token", lambda _uid: "new_access_token")
		mock_repos["token_repo"].get_unused_token.return_value = MagicMock()

		result = await auth_service.refresh_access_token("valid_refresh_token")

		assert result["access_token"] == "new_access_token"
		mock_repos["token_repo"].get_unused_token.assert_awaited_once_with("some-uuid")

	async def test_refresh_token_revoked(self, auth_service, mock_repos, monkeypatch):
		monkeypatch.setattr("app.core.security.decode_token", lambda _t: {"type": "refresh", "sub": "99", "jti": "revoked-jti"})
		mock_repos["token_repo"].get_unused_token.return_value = None

		with pytest.raises(ValueError, match = "Refresh token has been revoked or used."):
			await auth_service.refresh_access_token("revoked_token")
