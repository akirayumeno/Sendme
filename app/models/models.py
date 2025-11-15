import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# Define the properties and behaviors of objects such as File and User.
class MessageType(enum.Enum):
	text = "text"
	image = "image"
	file = "file"


class MessageStatus(enum.Enum):
	uploaded = "UPLOADED"
	processing = "PROCESSING"
	deleted = "DELETED"
	failed = "FAILED"


class DeviceType(enum.Enum):
	phone = "phone"
	desktop = "desktop"


class Message(Base):
	__tablename__ = "messages"

	id = Column(Integer, primary_key = True, index = True)
	type = Column(Enum(MessageType), nullable = False)
	status = Column(Enum(MessageStatus), default = MessageStatus.uploaded, nullable = False)
	is_deleted = Column(Boolean, nullable = False, default = False)
	mime_type = Column(String(100), nullable = True)

	# User
	user_id = Column(Integer, ForeignKey("users.id"), nullable = False)  # Foreign key to link to User

	# Text content
	content = Column(Text, nullable = True)

	# File content
	file_id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
	file_name = Column(String(255), nullable = True)
	file_size = Column(Integer, nullable = True)
	file_path = Column(String(500), nullable = True)
	original_filename = Column(String(255), nullable = True)

	# Metadata
	device = Column(Enum(DeviceType), default = DeviceType.desktop)
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
	max_quota_bytes = Column(Integer, nullable = True)
	# Minimum total storage space (bytes) allowed for user uploads.
	used_quota_bytes = Column(Integer, nullable = True)
	is_active = Column(Boolean, nullable = False, default = True)
	hashed_password = Column(String, nullable = False)
	created_at = Column(DateTime, default = datetime.utcnow)
	updated_at = Column(
		DateTime(timezone = True), default = lambda:datetime.now(timezone.utc),
		onupdate = lambda:datetime.now(timezone.utc)
	)
	
	# Message relationship
	messages = relationship("Message", back_populates = "owner")
