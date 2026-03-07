from app.core.enums import MessageStatus
from app.core.orm_models import Message
from app.schemas.schemas import TextMessageCreate
from app.storage.sqlalchemy_repo import MessageRepository, UserRepository


class MessageService:
	def __init__(
			self,
			message_repo: MessageRepository,
			user_repo: UserRepository,
	):
		self.message_repo = message_repo
		self.user_repo = user_repo

	async def create_text_message(
			self, schema: TextMessageCreate
	) -> Message:
		"""text message save in database"""
		data = schema.model_dump()
		data["status"] = MessageStatus.sent
		return await self.message_repo.create_message(data)

	async def get_history(self, user_id: int, limit: int = 20, offset: int = 0):
		"""get history from user"""
		return await self.message_repo.get_by_user(user_id, limit, offset)

	async def delete_message(self, message_id: int, user_id: int) -> Message:
		"""delete message by id"""
		file_size = self.message_repo.delete_message(message_id)
