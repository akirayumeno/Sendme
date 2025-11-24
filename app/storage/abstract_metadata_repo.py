from abc import ABC, abstractmethod
from typing import Optional, List

from app.core.orm_models import Message, User


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
	def delete_message(self, message_id: int):
		raise NotImplementedError


class AbstractCapacityRepository(ABC):
	"""Abstract capacity repository interface."""

	@abstractmethod
	def get_used_capacity(self, user_id: int) -> Optional[int]:
		raise NotImplementedError

	@abstractmethod
	def get_capacity_by_user_id(self, user_id: int) -> Optional[int]:
		raise NotImplementedError

	@abstractmethod
	def update_used_capacity(self, user_id: int, byte_change: int):
		raise NotImplementedError
