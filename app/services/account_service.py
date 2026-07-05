from app.core.enums import MessageType
from app.services.file_service import FileService
from app.storage.redis_repo import RedisRepo
from app.storage.sqlalchemy_repo import MessageRepository, RefreshTokenRepository, UserRepository


class AccountService:
	def __init__(
			self,
			user_repo: UserRepository,
			message_repo: MessageRepository,
			token_repo: RefreshTokenRepository,
			file_service: FileService,
			redis_repo: RedisRepo,
	):
		self.user_repo = user_repo
		self.message_repo = message_repo
		self.token_repo = token_repo
		self.file_service = file_service
		self.redis_repo = redis_repo

	async def delete_account(self, user_id: int) -> dict:
		user = await self.user_repo.get_user_by_id(user_id)
		messages = await self.message_repo.get_all_by_user(user_id)

		deleted_messages = 0
		for message in messages:
			if self._has_physical_file(message):
				await self.file_service.delete_existing_file(message.id, user_id)
			else:
				await self.message_repo.delete_message(message.id)
				await self.redis_repo.delete_timer(message.id)
			deleted_messages += 1

		await self.token_repo.delete_all_user_tokens(user_id)
		await self.redis_repo.clear_otp_state(user.email)
		await self.redis_repo.clear_otp_attempts(user.email)
		await self.user_repo.delete_user(user_id)

		return {"status":"success", "deleted_messages":deleted_messages}

	def _has_physical_file(self, message) -> bool:
		file_path = getattr(message, "file_path", None)
		return (isinstance(file_path, str) and bool(file_path)) or message.type in (MessageType.file, MessageType.image)
