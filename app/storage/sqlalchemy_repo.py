from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MessageStatus
from app.core.orm_models import User, Message, RefreshToken
from app.storage.abstract_metadata_repo import (
	AbstractUserRepository,
	AbstractMessageRepository,
	AbstractRefreshTokenRepository
)
from app.storage.exceptions import (
	UserConstraintError, RepositoryError, MessageNotFoundError,
	UserNotFoundErrorById, MessageUpdateError
)


# SQLAlchemy (PostgreSQL, MySQL, etc.)
# Asynchronous I/O using AsyncSession and asyncpg driver.
# Structured data (Metadata): User ID, username, password hash, message text, file path, etc.
class UserRepository(AbstractUserRepository):
	"""Implementation of user storage using AsyncSession."""

	def __init__(self, db: AsyncSession):
		self.db = db

	async def get_user_by_id(self, user_id: int) -> 'User':
		"""Retrieve the user from the database based on the user ID."""
		result = await self.db.execute(select(User).filter(User.id == user_id))
		user = result.scalars().first()
		if user is None:
			raise UserNotFoundErrorById(user_id)
		return user

	async def get_user_by_username(self, username: str) -> Optional[User]:
		"""Find a user by username (used for login verification)."""
		result = await self.db.execute(select(User).filter(User.username == username))
		user = result.scalars().first()
		return user

	async def create_user(self, username: str, hashed_password: str) -> User:
		"""Create a new user record in the database."""
		new_user = User(username = username, hashed_password = hashed_password)
		try:
			self.db.add(new_user)
			await self.db.commit()
			await self.db.refresh(new_user)
			return new_user
		except IntegrityError as e:
			await self.db.rollback()
			raise UserConstraintError(f"User {username} already exists in the database.") from e
		except Exception as e:
			await self.db.rollback()
			raise RepositoryError(f"An unknown error occurred while creating a user {username}.") from e

	async def update_user(self, user_id: int, updates: dict) -> User:
		"""Update a user record in the database."""
		user = await self.get_user_by_id(user_id)
		current_uid = user.id
		for key, value in updates.items():
			if hasattr(user, key):
				setattr(user, key, value)
		try:
			await self.db.commit()
			await self.db.refresh(user)
			return user
		except IntegrityError as e:
			await self.db.rollback()
			raise UserConstraintError(f"Update failed due to constraint violation {current_uid}.") from e
		except Exception as e:
			await self.db.rollback()
			raise RepositoryError(f"Error updating user {current_uid}.") from e

	# ---Capacity method---
	async def get_user_with_capacity_lock(self, user_id: int) -> User:
		"""Pessimistic Locking to guarantee the atomicity of capacity updates."""
		stmt = select(User).filter(User.id == user_id).with_for_update()
		result = await self.db.execute(stmt)
		user = result.scalars().first()
		if user is None:
			raise UserNotFoundErrorById(user_id)
		return user

	async def get_capacity_by_user_id(self, user_id: int) -> Optional[int]:
		stmt = select(User.max_quota_bytes).filter(User.id == user_id)
		result = await self.db.execute(stmt)
		return result.scalar()

	async def get_used_capacity(self, user_id: int) -> int:
		stmt = select(User.used_quota_bytes).filter(User.id == user_id)
		result = await self.db.execute(stmt)
		used_quota_bytes = result.scalar()
		return used_quota_bytes if used_quota_bytes is not None else 0

	async def update_used_capacity(self, user_id: int, byte_change: int) -> int:
		user = await self.get_user_with_capacity_lock(user_id)
		user.used_quota_bytes += byte_change
		await self.db.commit()
		return user.used_quota_bytes


class MessageRepository(AbstractMessageRepository):
	"""Implementation of message storage using AsyncSession."""

	def __init__(self, db: AsyncSession):
		self.db = db

	async def create_message(self, data: dict) -> Message:
		new_message = Message(**data)
		try:
			self.db.add(new_message)
			await self.db.commit()
			await self.db.refresh(new_message)
			return new_message
		except Exception as e:
			await self.db.rollback()
			raise RepositoryError(f"Error creating message: {e}") from e

	async def get_message_by_message_id(self, message_id: int) -> Optional[Message]:
		result = await self.db.execute(select(Message).filter(Message.id == message_id))
		message = result.scalars().first()
		if message is None:
			raise MessageNotFoundError(message_id = message_id)
		return message

	async def get_messages_by_user(self, user_id: int) -> List['Message']:
		result = await self.db.execute(select(Message).filter(Message.user_id == user_id))
		return list(result.scalars().all())

	async def update_message(self, message_id: int, status: MessageStatus):
		message = await self.get_message_by_message_id(message_id)
		try:
			message.status = status
			await self.db.commit()
			await self.db.refresh(message)
		except Exception:
			await self.db.rollback()
			raise MessageUpdateError(message_id = message_id)

	async def delete_message(self, message_id: int) -> Optional[int]:
		"""Permanently delete the message record and return the file size for capacity deduction."""
		# 1. Get the file size first
		stmt_size = select(Message.file_size_bytes).filter(Message.id == message_id)
		result_size = await self.db.execute(stmt_size)
		file_size = result_size.scalar()

		if file_size is None:
			return None

		try:
			# 2. Perform deletion
			await self.db.execute(delete(Message).filter(Message.id == message_id))
			await self.db.commit()
			return file_size
		except Exception as e:
			await self.db.rollback()
			raise RepositoryError(f"Error hard deleting message {message_id}: {e}") from e


class RefreshTokenRepository(AbstractRefreshTokenRepository):
	def __init__(self, db: AsyncSession):
		self.db = db

	async def create_token_record(self, user_id: int, token_jti: str, expires_at: datetime) -> RefreshToken:
		new_token = RefreshToken(
			jti = token_jti,
			user_id = user_id,
			expires_at = expires_at,
		)
		try:
			self.db.add(new_token)
			await self.db.commit()
			await self.db.refresh(new_token)
			return new_token
		except Exception as e:
			await self.db.rollback()
			raise RepositoryError(f"Error creating token {token_jti}: {e}") from e

	async def get_unused_token(self, token_jti: str) -> Optional[RefreshToken]:
		stmt = select(RefreshToken).filter(
			RefreshToken.jti == token_jti,
			RefreshToken.expires_at > func.now()
		)
		result = await self.db.execute(stmt)
		unused_token = result.scalars().first()
		if not unused_token:
			raise RepositoryError(f"Refresh Token {token_jti} not found or already used.")
		return unused_token

	async def delete_token_record(self, token_jti: str) -> bool:
		try:
			await self.db.execute(delete(RefreshToken).filter(RefreshToken.jti == token_jti))
			await self.db.commit()
			return True
		except Exception as e:
			await self.db.rollback()
			raise RepositoryError(f"Error deleting token {token_jti}: {e}") from e

	async def delete_all_user_tokens(self, user_id: int) -> int:
		try:
			stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id)
			result = await self.db.execute(stmt)
			await self.db.commit()
			return result.rowcount
		except Exception as e:
			await self.db.rollback()
			raise RepositoryError(f"Error deleting all tokens for user {user_id}: {e}") from e
