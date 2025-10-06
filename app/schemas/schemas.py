from uuid import UUID
from pydantic import BaseModel, computed_field, field_validator, ValidationInfo
from typing import Optional, ClassVar
from datetime import datetime
from enum import Enum

# Data validation and serialization
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
	# UUID 类型是正确的，Pydantic V2 会自动将其序列化为字符串
	id: UUID
	type: MessageType
	status: MessageStatus
	content: Optional[str] = None
	fileName: Optional[str] = None
	fileSize: Optional[int] = None
	file_type: Optional[str] = None  # 注意：这里应该是 file_type 而不是 fileType (Python 习惯)
	filePath: Optional[str] = None
	device: DeviceType
	created_at: datetime

	class Config:
		# Pydantic V2 中 from_attributes=True 已经成为默认行为，但保留无害
		from_attributes = True

	@computed_field
	@property
	def imageUrl(self) -> Optional[str]:
		"""Generate image URL for image types"""

		# computed_field 方法可以直接通过 self 访问其他字段
		if self.type == MessageType.image and self.filePath:
			return f"/files/{self.filePath}"

		return None  # 如果不是 image 或没有 path，返回 None