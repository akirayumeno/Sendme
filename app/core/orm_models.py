import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum

from app.core.enums import MessageType, MessageStatus, DeviceType

Base = declarative_base()


# Define the properties and behaviors of objects such as File and User.
# For repository layer

class Message(Base):
	__tablename__ = "messages"

	id = Column(Integer, primary_key = True, index = True)
	type = Column(SQLAlchemyEnum(MessageType, name = 'message_type'), nullable = False)
	status = Column(SQLAlchemyEnum(MessageStatus), default = MessageStatus.processing, nullable = False)
	is_deleted = Column(Boolean, nullable = False, default = False)
	mime_type = Column(String(100), nullable = True)

	# User
	user_id = Column(Integer, ForeignKey("users.id"), nullable = False)  # Foreign key to link to User

	# Text content
	content = Column(Text, nullable = True)

	# File content
	file_id = Column(UUID(as_uuid = True), default = uuid.uuid4, nullable = True)
	file_name = Column(String(255), nullable = True)
	file_size = Column(Integer, nullable = True)
	file_path = Column(String(500), nullable = True)
	original_filename = Column(String(255), nullable = True)

	# Metadata
	device = Column(SQLAlchemyEnum(DeviceType), default = DeviceType.desktop)
	owner = relationship("User", back_populates = "messages")  # Message owner relationship
	created_at = Column(DateTime(timezone = True), default = lambda:datetime.now(timezone.utc))
	updated_at = Column(
		DateTime(timezone = True), default = lambda:datetime.now(timezone.utc),
		onupdate = lambda:datetime.now(timezone.utc)
	)


class User(Base):
	__tablename__ = "users"
	id = Column(Integer, primary_key = True, index = True)
	username = Column(String(255), unique = True, index = True, nullable = False)
	# Maximum total storage space (bytes) allowed for user uploads.
	max_quota_bytes = Column(Integer, nullable = False, default = 100 * 1024 * 1024)
	# Minimum total storage space (bytes) allowed for user uploads.
	used_quota_bytes = Column(Integer, default = 0)
	hashed_password = Column(String, nullable = False)
	is_verified = Column(Boolean, nullable = False, default = False)
	created_at = Column(DateTime, default = datetime.now(timezone.utc))
	updated_at = Column(
		DateTime(timezone = True), default = lambda:datetime.now(timezone.utc),
		onupdate = lambda:datetime.now(timezone.utc)
	)

	# Message relationship
	messages = relationship("Message", back_populates = "owner")
	refresh_tokens = relationship("RefreshToken", back_populates = "user")


class RefreshToken(Base):
	"""A database model for refresh tokens. Used to store token records and implement token revocability."""
	__tablename__ = "refresh_tokens"
	jti = Column(String(36), primary_key = True, index = True, nullable = False)
	user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
	expires_at = Column(DateTime(timezone = True), nullable = False)
	is_used = Column(Boolean, nullable = False, default = False)
	created_at = Column(DateTime, default = datetime.now(timezone.utc), server_default = func.now())
	user = relationship("User", back_populates = "refresh_tokens")

	def __repr__(self):
		return f"<RefreshToken(jti={self.jti}, user_id={self.user_id}, expires_at={self.expires_at})>"
