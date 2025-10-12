from uuid import UUID
from pydantic import BaseModel, computed_field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
	text = "text"
	image = "image"
	file = "file"


class MessageStatus(str, Enum):
	uploading = "uploading"
	success = "success"
	error = "error"


class DeviceType(str, Enum):
	phone = "phone"
	desktop = "desktop"


class MessageBase(BaseModel):
	type: MessageType
	device: DeviceType = DeviceType.desktop


class TextMessageCreate(MessageBase):
	content: str
	type: MessageType = MessageType.text

	@field_validator('content')
	@classmethod
	def content_must_not_be_empty(cls, v: str) -> str:
		if not v.strip():
			raise ValueError('Content cannot be empty')
		return v


class FileMessageCreate(MessageBase):
	fileName: str
	fileSize: int
	fileType: str
	filePath: str
	type: MessageType


class SimulateUploadRequest(BaseModel):
	fileName: str
	fileSize: int
	fileType: str


class MessageResponse(BaseModel):
	"""Response model that matches frontend Message interface exactly"""
	id: str
	type: MessageType
	status: MessageStatus

	# Text content
	content: Optional[str] = None

	# File content - matching frontend field names
	fileName: Optional[str] = None
	fileSize: Optional[str] = None
	fileType: Optional[str] = None
	imageUrl: Optional[str] = None

	# Upload progress
	progress: Optional[int] = None
	error: Optional[str] = None

	# Metadata - matching frontend field names
	timestamp: str
	device: str
	copied: bool = False

	class Config:
		from_attributes = True

	@computed_field
	@property
	def image_url(self) -> Optional[str]:
		"""Generate image URL for image types"""
		# This will be set from filePath in the model conversion
		return None

	@classmethod
	def from_db_model(cls, db_message, base_url: str = ""):
		"""Convert database model to response model with proper formatting"""
		# Format file size to string with units
		file_size_str = None
		if db_message.file_size:
			file_size_str = cls._format_file_size(db_message.file_size)

		# Format timestamp to match frontend format
		timestamp = db_message.created_at.strftime('%I:%M %p')

		# Generate imageUrl for image types
		image_url = None
		if db_message.type.value == 'image' and db_message.file_path:
			image_url = f"{base_url}/files/{db_message.file_path}"

		return cls(
			id=str(db_message.id),
			type=db_message.type.value,
			status=db_message.status.value,
			content=db_message.content,
			fileName=db_message.file_name,
			fileSize=file_size_str,
			fileType=db_message.file_type,
			imageUrl=image_url,
			progress=None,  # Not stored in DB, only used during upload
			error=None,  # Could be added to DB if needed
			timestamp=timestamp,
			device=db_message.device.value,
			copied=False
		)

	@staticmethod
	def _format_file_size(bytes: int) -> str:
		"""Format bytes to human-readable string"""
		if bytes == 0:
			return "0 Bytes"
		k = 1024
		sizes = ["Bytes", "KB", "MB", "GB"]
		i = 0
		size = float(bytes)
		while size >= k and i < len(sizes) - 1:
			size /= k
			i += 1
		return f"{round(size, 1)} {sizes[i]}"