from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, computed_field, field_validator, ConfigDict, Field
from typing import Optional
from enum import Enum

BASE_URL = "http://localhost:8000/api/v1"


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


def format_file_size(bytes: int) -> str:
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


class MessageResponse(BaseModel):
	"""Response model that matches frontend Message interface exactly"""
	id: str
	type: MessageType
	status: MessageStatus

	# Text content
	content: Optional[str] = None

	# File content - matching frontend field names
	fileName: Optional[str] = Field(None, alias="file_name")
	fileType: Optional[str] = Field(None, alias="file_type")

	file_path_raw: Optional[str] = Field(None, alias="file_path")
	file_size_int: Optional[int] = Field(None, alias="file_size", exclude=True)

	# Upload progress
	progress: Optional[int] = None
	error: Optional[str] = None

	# Metadata
	created_at: datetime
	updated_at: datetime
	device: str
	copied: bool = False

	# Pydantic v2 config
	model_config = ConfigDict(
		from_attributes=True,
		populate_by_name=True,
		json_encoders={
			UUID: str
		},
	)

	@field_validator('id', mode='before')
	@classmethod
	def validate_id(cls, v):
		# Check if the input value is of type UUID (from the database)
		if isinstance(v, UUID):
			return str(v)
		# Otherwise return it as is (maybe it's already a string, or some other type for Pydantic to handle)
		return v

	@computed_field
	@property
	def imageUrl(self) -> Optional[str]:
		"""Generate image URL for image types"""
		if self.type == MessageType.image and self.file_path_raw:
			return f"{BASE_URL}/files/{self.file_path_raw}"
		return None

	@computed_field
	@property
	def fileSize(self) -> Optional[str]:
		"""Format raw file_size (int) to human-readable string (str)"""
		if self.file_size_int is not None:
			return format_file_size(self.file_size_int)
		return None