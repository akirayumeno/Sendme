from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import router as auth_router
from app.core.dependencies import get_account_service, get_auth_service, get_current_user_id
from app.services.exceptions import OtpInvalidError, RateLimitError


def build_app(auth_service: AsyncMock) -> TestClient:
	app = FastAPI()
	app.include_router(auth_router, prefix="/api/v1")
	app.dependency_overrides[get_auth_service] = lambda: auth_service
	return TestClient(app)


def test_request_otp_success():
	service = AsyncMock()
	service.request_register_otp.return_value = {"message": "Verification code sent."}
	client = build_app(service)

	resp = client.post(
		"/api/v1/auth/request-otp",
		json={"email": "u@example.com", "username": "user1", "password": "password123"},
	)

	assert resp.status_code == 200
	assert resp.json()["message"] == "Verification code sent."


def test_request_otp_rate_limit():
	service = AsyncMock()
	service.request_register_otp.side_effect = RateLimitError("too fast")
	client = build_app(service)

	resp = client.post(
		"/api/v1/auth/request-otp",
		json={"email": "u@example.com", "username": "user1", "password": "password123"},
	)

	assert resp.status_code == 429
	assert resp.json()["detail"] == "too fast"


def test_register_with_otp_invalid():
	service = AsyncMock()
	service.register_with_otp.side_effect = OtpInvalidError("bad otp")
	client = build_app(service)

	resp = client.post(
		"/api/v1/auth/register-with-otp",
		json={"email": "u@example.com", "otp_code": "123456"},
	)

	assert resp.status_code == 400
	assert resp.json()["detail"] == "bad otp"


def test_login_invalid_credentials():
	service = AsyncMock()
	service.login.side_effect = ValueError("Invalid username or password.")
	client = build_app(service)

	resp = client.post(
		"/api/v1/auth/login",
		data={"username": "user1", "password": "wrong"},
	)

	assert resp.status_code == 401


def test_refresh_success():
	service = AsyncMock()
	service.refresh_access_token.return_value = {"access_token": "new-token", "token_type": "bearer"}
	client = build_app(service)

	resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "refresh-token"})

	assert resp.status_code == 200
	assert resp.json()["access_token"] == "new-token"


def test_delete_account_success():
	auth_service = AsyncMock()
	account_service = AsyncMock()
	account_service.delete_account.return_value = {"status":"success", "deleted_messages":2}
	app = FastAPI()
	app.include_router(auth_router, prefix="/api/v1")
	app.dependency_overrides[get_auth_service] = lambda: auth_service
	app.dependency_overrides[get_account_service] = lambda: account_service
	app.dependency_overrides[get_current_user_id] = lambda: 1
	client = TestClient(app)

	resp = client.delete("/api/v1/auth/account")

	assert resp.status_code == 200
	assert resp.json() == {"status":"success", "deleted_messages":2}
	account_service.delete_account.assert_awaited_once_with(1)
