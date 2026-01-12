from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List

from app.core.enums import MessageStatus
from app.core.orm_models import Message, User, RefreshToken


class AbstractUserRepository(ABC):
	"""Abstract user repository interface."""

	@abstractmethod
	def get_user_by_id(self, user_id: int) -> User:
		raise NotImplementedError

	@abstractmethod
	def get_user_by_username(self, username: str) -> Optional[User]:
		raise NotImplementedError

	@abstractmethod
	def create_user(self, username: str, hashed_password: str) -> User:
		raise NotImplementedError

	# ---Capacity---
	@abstractmethod
	def get_user_with_capacity_lock(self, user_id: int) -> Optional[int]:
		raise NotImplementedError

	@abstractmethod
	def get_used_capacity(self, user_id: int) -> Optional[int]:
		raise NotImplementedError

	@abstractmethod
	def get_capacity_by_user_id(self, user_id: int) -> Optional[int]:
		raise NotImplementedError

	@abstractmethod
	def update_used_capacity(self, user_id: int, byte_change: int):
		raise NotImplementedError


class AbstractMessageRepository(ABC):
	"""Abstract message repository interface."""

	@abstractmethod
	def get_message_by_message_id(self, message_id: int) -> Optional['Message']:
		raise NotImplementedError

	@abstractmethod
	def create_message(self, data: dict) -> Message:
		raise NotImplementedError

	@abstractmethod
	def get_messages_by_user(self, user_id: int) -> List[Message]:
		raise NotImplementedError

	@abstractmethod
	def update_message(self, message_id: int, status: MessageStatus):
		raise NotImplementedError

	@abstractmethod
	def soft_delete_message(self, message_id: int):
		raise NotImplementedError

	@abstractmethod
	def restore_message(self, message_id: int) -> Message:
		raise NotImplementedError

	@abstractmethod
	def hard_delete_message(self, message_id: int) -> Optional[int]:
		raise NotImplementedError


class AbstractRefreshTokenRepository(ABC):
	"""Abstract refresh token repository interface."""

	@abstractmethod
	def create_token_record(self, user_id: int, token_jti: str, expires_at: datetime) -> RefreshToken:
		raise NotImplementedError

	@abstractmethod
	def get_unused_token(self, token_jti: str) -> Optional[RefreshToken]:
		raise NotImplementedError

	@abstractmethod
	def mark_token_as_used(self, token_jti: str) -> RefreshToken:
		raise NotImplementedError

	@abstractmethod
	def delete_token_record(self, token_jti: str) -> bool:
		raise NotImplementedError

	@abstractmethod
	def delete_all_user_tokens(self, user_id: int) -> int:
		"""Delete all unused refresh tokens for the user (force exit all devices)"""
		raise NotImplementedError
