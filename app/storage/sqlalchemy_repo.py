from datetime import datetime
from typing import Optional, List

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import MessageStatus
from app.core.orm_models import User, Message, RefreshToken
from app.storage.abstract_metadata_repo import AbstractUserRepository, \
	AbstractMessageRepository, AbstractRefreshTokenRepository
from app.storage.exceptions import UserConstraintError, RepositoryError, MessageNotFoundError, \
	UserNotFoundErrorById, UserNotFoundErrorByName, MessageRestoreError, MessageUpdateError


# SQLAlchemy (PostgresSQL, MySQL, etc.)
# Blocking/non-blocking I/O (depending on the ORM), but the data structure is relational.
# Structured data (Metadata): User ID, username, password hash, message text, file path, etc.
class UserRepository(AbstractUserRepository):
	"""Implementation of user storage."""

	def __init__(self, db: Session):
		self.db = db

	def get_user_by_id(self, user_id: int) -> 'User':
		"""Retrieve the user from the database based on the user ID."""
		user = self.db.query(User).filter(User.id == user_id).first()
		if user is None:
			raise UserNotFoundErrorById(user_id)
		return user

	def get_user_by_username(self, username: str) -> Optional[User]:
		"""Find a user by username (used for login verification)"""
		user = self.db.query(User).filter(User.username == username).first()
		if user is None:
			raise UserNotFoundErrorByName(username)
		return user

	def create_user(self, username: str, hashed_password: str) -> User:
		"""Create a new user record in the database."""
		new_user = User(username = username, hashed_password = hashed_password)
		try:
			self.db.add(new_user)
			self.db.commit()
			self.db.refresh(new_user)
			return new_user
		except IntegrityError as e:
			self.db.rollback()
			raise UserConstraintError(f"User {username} already exists in the database.") from e

		except Exception as e:
			self.db.rollback()
			raise RepositoryError(f"An unknown error occurred while creating a user{username}.") from e

	def update_user(self, user_id: int, updates: dict) -> User:
		"""Update a user record in the database."""
		user = self.get_user_by_id(user_id)
		current_uid = user.id
		for key, value in updates.items():
			if hasattr(user, key):
				setattr(user, key, value)
		try:
			self.db.commit()
			self.db.refresh(user)
			return user
		except IntegrityError as e:
			self.db.rollback()
			raise UserConstraintError(f"Update failed due to constraint violation {current_uid}.") from e
		except Exception as e:
			self.db.rollback()
			raise RepositoryError(f"Error updating user{current_uid}.") from e

	# ---Capacity method---
	def get_user_with_capacity_lock(self, user_id: int) -> User:
		# Pessimistic Locking to guarantee the atomicity of capacity updates
		user = self.db.query(User).filter(User.id == user_id).with_for_update().first()
		if user is None:
			raise UserNotFoundErrorById(user_id)
		return user

	def get_capacity_by_user_id(self, user_id: int) -> Optional[int]:
		max_quota_bytes = self.db.query(User.max_quota_bytes).filter(User.id == user_id).scalar()
		return max_quota_bytes

	def get_used_capacity(self, user_id: int) -> int:
		used_quota_bytes = self.db.query(User.used_quota_bytes).filter(User.id == user_id).scalar()
		return used_quota_bytes if used_quota_bytes is not None else 0

	def update_used_capacity(self, user_id: int, byte_change: int) -> int:
		user = self.get_user_with_capacity_lock(user_id)
		user.used_quota_bytes += byte_change
		self.db.commit()
		return user.used_quota_bytes


class MessageRepository(AbstractMessageRepository):
	"""Implementation of message storage."""

	def __init__(self, db: Session):
		self.db = db

	def create_message(self, data: dict) -> Message:
		new_message = Message(**data)
		try:
			self.db.add(new_message)
			self.db.commit()
			self.db.refresh(new_message)
			return new_message
		except Exception as e:
			self.db.rollback()
			raise RepositoryError(f"Error creating message: {e}") from e

	def get_message_by_message_id(self, message_id: int) -> Optional[Message]:
		message = self.db.query(Message).filter(Message.id == message_id).first()
		if message is None:
			raise MessageNotFoundError(message_id = message_id)
		return message

	def get_messages_by_user(self, user_id: int) -> List['Message']:
		messages = self.db.query(Message).filter(Message.user_id == user_id).all()
		return messages

	def update_message(self, message_id: int, status: MessageStatus):
		message = self.get_message_by_message_id(message_id)
		try:
			message.status = status
			self.db.commit()
			self.db.refresh(message)
		except Exception:
			self.db.rollback()
			raise MessageUpdateError(message_id = message_id)

	def soft_delete_message(self, message_id: int):
		message = self.get_message_by_message_id(message_id)
		try:
			message.is_deleted = True
			self.db.commit()
		except Exception as e:
			self.db.rollback()
			raise RepositoryError(f"Error deleting message {message_id}: {e}") from e

	def restore_message(self, message_id: int) -> Message:
		"""Set the message's soft delete flag (is_deleted) back to False to enable the undo function."""
		message = self.get_message_by_message_id(message_id)
		try:
			if message.is_deleted:
				message.is_deleted = False
				self.db.commit()
				self.db.refresh(message)
			return message
		except Exception as e:
			self.db.rollback()
			raise MessageRestoreError(message_id = message_id)

	def hard_delete_message(self, message_id: int) -> Optional[int]:
		"""Permanently delete the message record and return the number of bytes occupied by the message (used for capacity deduction)."""
		result = self.db.query(
			Message.file_size_bytes,
			Message.is_deleted
		).filter(Message.id == message_id).first()
		if not result:
			return None  # The message does not exist and requires no processing.
		file_size, is_deleted = result

		# Check if it has been marked as a soft delete; if not, it should not be hard deleted.
		if not is_deleted:
			return 0
		try:
			# Perform deletion
			deleted_count = self.db.query(Message).filter(
				Message.id == message_id
			).delete(synchronize_session = 'fetch')
			if deleted_count == 0:
				return None
			self.db.commit()

			# The returned file size allows the Service layer to call UserRepository to deduct the required capacity.
			return file_size
		except Exception as e:
			self.db.rollback()
			raise RepositoryError(f"Error hard deleting message {message_id}: {e}") from e


class RefreshTokenRepository(AbstractRefreshTokenRepository):
	def __init__(self, db: Session):
		self.db = db

	def create_token_record(self, user_id: int, token_jti: str, expires_at: datetime) -> RefreshToken:
		new_token = RefreshToken(
			jti = token_jti,
			user_id = user_id,
			expires_at = expires_at,
			is_used = False
		)
		try:
			self.db.add(new_token)
			self.db.commit()
			self.db.refresh(new_token)
			return new_token
		except IntegrityError as e:
			self.db.rollback()
			raise UserConstraintError(f"Token {token_jti} already exists in the database.") from e
		except Exception as e:
			self.db.rollback()
			raise RepositoryError(f"Error creating token {token_jti}: {e}") from e

	def get_unused_token(self, token_jti: str) -> Optional[RefreshToken]:
		unused_token = self.db.query(RefreshToken).filter(
			RefreshToken.jti == token_jti,
			RefreshToken.is_used == False,  # assure that it isn't used
			RefreshToken.expires_at > func.now()  # assure that it's not expired
		).first()
		if not unused_token:
			raise RepositoryError(f"Refresh Token {token_jti} not found or already used.")
		return unused_token

	def mark_token_as_used(self, token_jti: str) -> Optional[RefreshToken]:
		unused_token = self.get_unused_token(token_jti)
		try:
			unused_token.is_used = True
			self.db.commit()
			self.db.refresh(unused_token)
			return unused_token
		except Exception as e:
			self.db.rollback()
			raise RepositoryError(f"Error marking token {token_jti} as used: {e}")

	def delete_token_record(self, token_jti: str) -> bool:
		deleted_rows = self.db.query(RefreshToken).filter(RefreshToken.jti == token_jti).delete()
		try:
			self.db.commit()
			return deleted_rows > 0
		except Exception as e:
			self.db.rollback()
			raise RepositoryError(f"Error deleting token {token_jti}: {e}") from e

	def delete_all_user_tokens(self, user_id: int) -> int:
		deleted_count = self.db.query(RefreshToken).filter(
			RefreshToken.user_id == user_id,
			RefreshToken.is_used == False
		).delete(synchronize_session = 'fetch')
		try:
			self.db.commit()
			return deleted_count
		except Exception as e:
			self.db.rollback()
			raise RepositoryError(f"Error deleting all tokens for user {user_id}: {e}") from e
