from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from starlette.exceptions import HTTPException

from app.api.router import get_auth_service
from app.core.security import AuthService
from app.services.exceptions import ServiceError

router_messages = APIRouter(
	tags = ["messages"]
)


@router_messages.post("/token")
async def login_for_access_token(
		form_data: OAuth2PasswordRequestForm = Depends(),
		auth_service: AuthService = Depends(get_auth_service)
):
	try:
		access_token = auth_service.login_user(
			username = form_data.username,
			password = form_data.password
		)

		return {"access_token":access_token, "token_type":"bearer"}

	except ServiceError as e:
		raise HTTPException(
			status_code = status.HTTP_400_BAD_REQUEST,
			detail = e.message
		)
