from typing import Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import UUID4


async def valid_post_id(post_id: UUID4) -> dict[str, Any]:
	post = await service.get_by_id(post_id)
	if not post:
		raise PostNotFound()

	return post


async def parse_jwt_data(
		token: str = Depends(OAuth2PasswordBearer(tokenUrl = "/auth/token"))
) -> dict[str, Any]:
	try:
		payload = jwt.decode(token, "JWT_SECRET", algorithms = ["HS256"])
	except JWTError:
		raise InvalidCredentials()

	return {"user_id":payload["id"]}


async def valid_owned_post(
		post: dict[str, Any] = Depends(valid_post_id),
		token_data: dict[str, Any] = Depends(parse_jwt_data),
) -> dict[str, Any]:
	if post["creator_id"] != token_data["user_id"]:
		raise UserNotOwner()

	return post


async def valid_active_creator(
		token_data: dict = Depends(parse_jwt_data),
):
	user = await users_service.get_by_id(token_data["user_id"])
	if not user["is_active"]:
		raise UserIsBanned()

	if not user["is_creator"]:
		raise UserNotCreator()

	return user
