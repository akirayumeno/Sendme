from app.core.enums import MessageStatus, MessageType
from app.core.orm_models import Message
from app.schemas.schemas import TextMessageCreate
from app.services.exceptions import MessageNotFoundError, MessagePermissionError
from app.services.file_service import FileService
from app.storage.sqlalchemy_repo import MessageRepository, UserRepository


class MessageService:
	def __init__(
			self,
			message_repo: MessageRepository,
			user_repo: UserRepository,
			file_service: FileService,
	):
		self.message_repo = message_repo
		self.user_repo = user_repo
		self.file_service = file_service

	async def create_text_message(
			self, schema: TextMessageCreate
	) -> Message:
		"""text message save in database"""
		data = schema.model_dump()
		data.update(
			{
				"status":MessageStatus.sent,
				"file_size_bytes":0
			}
		)
		return await self.message_repo.create_message(data)

	async def get_history(self, user_id: int, page: int = 1, page_size: int = 20):
		"""get history from user"""
		offset = (max(1, page) - 1) * page_size
		return await self.message_repo.get_by_user(user_id, page_size, offset)

	async def delete_message(self, message_id: int, user_id: int) -> bool:
		"""delete message by id"""
		# check the permission
		msg = await self.message_repo.get_by_message_id(message_id)

		if not msg:
			raise MessageNotFoundError("Message not found.")
		if msg.user_id != user_id:
			raise MessagePermissionError("Message Permission denied.")

		# when it's file
		if msg.type == MessageType.file:
			await self.file_service.delete_existing_file(message_id, user_id)
		# when it's text
		else:
			await self.message_repo.delete_message(message_id)
		return True
