from pydantic import BaseModel, validator
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

	@validator('content')
	def content_must_not_be_empty(cls, v):
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
	id: str
	type: MessageType
	status: MessageStatus
	content: Optional[str] = None
	fileName: Optional[str] = None
	fileSize: Optional[int] = None
	fileType: Optional[str] = None
	filePath: Optional[str] = None
	imageUrl: Optional[str] = None
	device: DeviceType
	created_at: datetime

	class Config:
		from_attributes = True

	@validator('imageUrl', always=True)
	def set_image_url(cls, v, values):
		"""Generate image URL for image types"""
		if values.get('type') == MessageType.image and values.get('filePath'):
			return f"/files/{values['filePath']}"
		return v
