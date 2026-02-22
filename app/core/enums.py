from enum import StrEnum


# Global enumeration type. Defines an Enum type that is shared across all modules.
class MessageType(StrEnum):
	text = "text"
	image = "image"
	file = "file"


class MessageStatus(StrEnum):
	sent = "SENT"
	processing = "PROCESSING"
	deleted = "DELETED"
	failed = "FAILED"
	expired = "EXPIRED"


class DeviceType(StrEnum):
	phone = "phone"
	desktop = "desktop"
