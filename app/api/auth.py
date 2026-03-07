from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.dependencies import get_auth_service
from app.schemas.schemas import RegisterWithOtpSchema, RequestOtpSchema
from app.services.auth_service import AuthService
from app.services.exceptions import EmailDeliveryError, OtpInvalidError, OtpLockedError, RateLimitError
from app.storage.exceptions import UserConstraintError

router = APIRouter(prefix = "/auth", tags = ["auth"])


class RefreshTokenRequest(BaseModel):
	refresh_token: str


@router.post("/request-otp")
async def request_otp(schema: RequestOtpSchema, auth_service: AuthService = Depends(get_auth_service)):
	try:
		return await auth_service.request_register_otp(
			email = str(schema.email),
			username = schema.username,
			password = schema.password,
		)
	except UserConstraintError as exc:
		raise HTTPException(status_code = 409, detail = str(exc)) from exc
	except RateLimitError as exc:
		raise HTTPException(status_code = 429, detail = str(exc)) from exc
	except OtpLockedError as exc:
		raise HTTPException(status_code = 423, detail = str(exc)) from exc
	except EmailDeliveryError as exc:
		raise HTTPException(status_code = 503, detail = str(exc)) from exc


@router.post("/register-with-otp")
async def register_with_otp(schema: RegisterWithOtpSchema, auth_service: AuthService = Depends(get_auth_service)):
	try:
		return await auth_service.register_with_otp(
			email = str(schema.email),
			otp_code = schema.otp_code,
		)
	except OtpInvalidError as exc:
		raise HTTPException(status_code = 400, detail = str(exc)) from exc
	except OtpLockedError as exc:
		raise HTTPException(status_code = 423, detail = str(exc)) from exc


@router.post("/login")
async def login(
		form_data: OAuth2PasswordRequestForm = Depends(),
		auth_service: AuthService = Depends(get_auth_service),
):
	try:
		return await auth_service.login(form_data.username, form_data.password)
	except ValueError as exc:
		raise HTTPException(status_code = 401, detail = str(exc)) from exc


@router.post("/refresh")
async def refresh(
		payload: RefreshTokenRequest,
		auth_service: AuthService = Depends(get_auth_service),
):
	try:
		return await auth_service.refresh_access_token(payload.refresh_token)
	except ValueError as exc:
		raise HTTPException(status_code = 401, detail = str(exc)) from exc
