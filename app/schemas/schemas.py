from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, computed_field, field_validator, ConfigDict, Field

from app.core.enums import MessageType, DeviceType, MessageStatus

# DTO (Data Transfer Object) for Service layer and API layer
BASE_URL = "http://localhost:8000/api/v1"


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
	user_id: int
	fileName: str
	fileSize: int
	fileType: str
	filePath: str
	type: str


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
	file_name: Optional[str] = Field(None, alias = "fileName")
	file_type: Optional[str] = Field(None, alias = "fileType")

	file_path: Optional[str] = Field(None, alias = "filePath")
	file_size: Optional[int] = Field(None, alias = "fileSize", exclude = True)

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
		from_attributes = True,
		populate_by_name = True,
		json_encoders = {
			UUID:str
		},
	)

	@field_validator('id', mode = 'before')
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
		if self.type == MessageType.image and self.file_path:
			return f"{BASE_URL}/view/{self.file_path}"
		return None

	@computed_field
	@property
	def fileSize(self) -> Optional[str]:
		"""Format raw file_size (int) to human-readable string (str)"""
		if self.file_size is not None:
			return format_file_size(self.file_size)
		return None


# User Schemas
class UserBase(BaseModel):
	username: str


class UserCreate(UserBase):
	password: str


class UserSchema(UserBase):
	id: int
	created_at: datetime

	class Config:
		orm_mode = True


# Authentication Token Schema
class Token(BaseModel):
	access_token: str
	token_type: str


class TokenData(BaseModel):
	username: Optional[str] = None
