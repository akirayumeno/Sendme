from sqlalchemy import Column, String, Integer, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
import enum

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

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	type = Column(Enum(MessageType), nullable=False)
	status = Column(Enum(MessageStatus), default=MessageStatus.success)

	# Text content
	content = Column(Text, nullable=True)

	# File content
	file_name = Column(String(255), nullable=True)
	file_size = Column(Integer, nullable=True)
	file_type = Column(String(100), nullable=True)
	file_path = Column(String(500), nullable=True)

	# Metadata
	device = Column(Enum(DeviceType), default=DeviceType.desktop)
	created_at = Column(DateTime, default=datetime.now())
	updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
