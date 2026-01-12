from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID

from pydantic import BaseModel, computed_field, field_validator, ConfigDict, Field

from app.core.enums import MessageType, DeviceType, MessageStatus
from app.core.utils import format_file_size

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
	file_name: str = Field(..., alias = "fileName")
	file_size: int = Field(..., gt = 0, alias = "fileSize")  # file size > 0
	file_type: str = Field(..., alias = "fileType")
	file_path: str = Field(..., alias = "filePath")
	type: MessageType = MessageType.file  # default as file

	model_config = ConfigDict(populate_by_name = True)


class MessageResponse(BaseModel):
	"""Response model that matches frontend Message interface exactly"""
	model_config = ConfigDict(from_attributes = True, populate_by_name = True)

	id: str
	type: MessageType
	status: MessageStatus

	# Text content
	content: Optional[str] = None

	# File content - matching frontend field names
	file_name: Optional[str] = Field(None, alias = "fileName")
	file_type: Optional[str] = Field(None, alias = "fileType")

	file_path: Optional[str] = Field(None, alias = "filePath")
	file_size_bytes: Optional[int] = Field(None, alias = "fileSize", exclude = True)

	# Upload progress
	progress: Optional[int] = None
	error: Optional[str] = None

	# Metadata
	created_at: datetime
	updated_at: datetime
	device: DeviceType
	copied: bool = False

	@field_validator('id', mode = 'before')
	@classmethod
	def validate_id(cls, v):
		return str(v) if isinstance(v, UUID) else v

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
		return format_file_size(self.file_size_bytes) if self.file_size_bytes else None


# User Schemas
class UserBase(BaseModel):
	# Usernames are restricted to contain only letters, numbers, and underscores, and must be 3-20 characters long.
	username: Annotated[str, Field(min_length = 3, max_length = 20, pattern = r"^[a-zA-Z0-9_]+$")]


class UserCreate(UserBase):
	password: str = Field(..., min_length = 8, description = "Password must be at least 8 characters")


class UserSchema(UserBase):
	id: int
	created_at: datetime

	model_config = ConfigDict(from_attributes = True)


# Authentication Token Schema
class Token(BaseModel):
	access_token: str
	token_type: str


class TokenData(BaseModel):
	username: Optional[str] = None
