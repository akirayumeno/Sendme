from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List

from app.core.enums import MessageStatus
from app.core.orm_models import Message, User, RefreshToken


class AbstractUserRepository(ABC):
	"""Abstract user repository interface (Asynchronous)."""

	@abstractmethod
	async def get_user_by_id(self, user_id: int) -> User:
		raise NotImplementedError

	@abstractmethod
	async def get_user_by_username(self, username: str) -> Optional[User]:
		raise NotImplementedError

	@abstractmethod
	async def create_user(self, username: str, hashed_password: str) -> User:
		raise NotImplementedError

	# ---Capacity---
	@abstractmethod
	async def get_user_with_capacity_lock(self, user_id: int) -> User:
		raise NotImplementedError

	@abstractmethod
	async def get_used_capacity(self, user_id: int) -> int:
		raise NotImplementedError

	@abstractmethod
	async def get_capacity_by_user_id(self, user_id: int) -> Optional[int]:
		raise NotImplementedError

	@abstractmethod
	async def update_used_capacity(self, user_id: int, byte_change: int) -> int:
		raise NotImplementedError


class AbstractMessageRepository(ABC):
	"""Abstract message repository interface (Asynchronous)."""

	@abstractmethod
	async def get_message_by_message_id(self, message_id: int) -> Optional['Message']:
		raise NotImplementedError

	@abstractmethod
	async def create_message(self, data: dict) -> Message:
		raise NotImplementedError

	@abstractmethod
	async def get_messages_by_user(self, user_id: int) -> List[Message]:
		raise NotImplementedError

	@abstractmethod
	async def update_message(self, message_id: int, status: MessageStatus):
		raise NotImplementedError

	@abstractmethod
	async def delete_message(self, message_id: int) -> Optional[int]:
		raise NotImplementedError


class AbstractRefreshTokenRepository(ABC):
	"""Abstract refresh token repository interface (Asynchronous)."""

	@abstractmethod
	async def create_token_record(self, user_id: int, token_jti: str, expires_at: datetime) -> RefreshToken:
		raise NotImplementedError

	@abstractmethod
	async def get_unused_token(self, token_jti: str) -> Optional[RefreshToken]:
		raise NotImplementedError

	@abstractmethod
	async def delete_token_record(self, token_jti: str) -> bool:
		raise NotImplementedError

	@abstractmethod
	async def delete_all_user_tokens(self, user_id: int) -> int:
		"""Delete all unused refresh tokens for the user (force exit all devices)"""
		raise NotImplementedError
