import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class MessageType(enum.Enum):
	text = "text"
	image = "image"
	file = "file"


class MessageStatus(enum.Enum):
	uploading = "uploading"
	success = "success"
	error = "error"


class DeviceType(enum.Enum):
	phone = "phone"
	desktop = "desktop"


class Message(Base):
	__tablename__ = "messages"

	id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
	user_id = Column(Integer, ForeignKey("users.id"), nullable = False)  # Foreign key to link to User

	type = Column(Enum(MessageType), nullable = False)
	status = Column(Enum(MessageStatus), default = MessageStatus.success)

	# Text content
	content = Column(Text, nullable = True)

	# File content
	file_name = Column(String(255), nullable = True)
	file_size = Column(Integer, nullable = True)
	file_type = Column(String(100), nullable = True)
	file_path = Column(String(500), nullable = True)

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
	username = Column(String, unique = True, index = True, nullable = False)
	hashed_password = Column(String, nullable = False)
	created_at = Column(DateTime, default = datetime.utcnow)

	# Message relationship
	messages = relationship("Message", back_populates = "owner")
