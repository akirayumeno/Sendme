from fastapi import FastAPI
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.services.exceptions import UserAuthenticationError


def register_exception_handlers(app: FastAPI):
	@app.exception_handler(UserAuthenticationError)
	def auth_error_handler(request: Request, exc: UserAuthenticationError):
		return JSONResponse(
			status_code = status.HTTP_401_UNAUTHORIZED,
			content = {"detail":exc.message},
			headers = {"WWW-Authenticate":"Bearer"},
		)
