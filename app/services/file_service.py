import uuid

from fastapi import UploadFile

from app.core.orm_models import Message
from app.core.settings import settings
from app.schemas.schemas import FileMessageCreate
from app.storage.file_repo import FileRepo
from app.storage.sqlalchemy_repo import MessageRepository, UserRepository


class FileService:
	"""
	Service responsible for coordinating file-related business logic,
	bridging the gap between physical storage (FileRepo) and database records (MessageRepo).
	"""

	def __init__(self, file_repo: FileRepo, message_repo: MessageRepository, user_repo: UserRepository):
		self.file_repo = file_repo
		self.message_repo = message_repo
		self.user_repo = user_repo

	async def handle_initial_upload(self, user_id: int, file: UploadFile) -> dict:
		"""
		Stage 1: Save the incoming stream to a temporary directory.
		This allows for file validation and 'Cancel' functionality before
		the message is officially created in the database.
		"""
		# Generate a unique temporary name to prevent collision
		temp_filename = f"{uuid.uuid4()}_{file.filename}"

		# Check capacity
		current_used = await self.user_repo.get_used_capacity(user_id)
		if current_used + (file.size or 0) > settings.DEFAULT_MAX_CAPACITY_BYTES:
			raise QuotaExceededError(
				
			)

		# Stream the file to the temp folder via Repo
		# If the connection is aborted, FileRepo handles the cleanup internally
		size_bytes = await self.file_repo.save(file.file, temp_filename, is_temp = True)

		return {
			"temp_filename":temp_filename,
			"original_filename":file.filename,
			"size_bytes":size_bytes,
			"mime_type":file.content_type
		}

	async def finalize_file_message(self, schema: FileMessageCreate) -> Message:
		return await self.message_repo.create_message(schema.model_dump())

	async def cancel_pending_upload(self, temp_filename: str):
		"""
		Action: Explicitly remove a file from temp storage if the user
		clicks 'X' on the UI before sending the message.
		"""
		return await self.file_repo.delete_temp(temp_filename)

	async def delete_existing_file(self, message_id: int, user_id: int) -> bool:
		"""
		Action: Permanent deletion.
		Removes both the physical file from disk and the record from the database.
		Includes owner validation to prevent unauthorized deletion.
		"""
		# 1. Fetch metadata to get the file path
		message = await self.message_repo.get_by_message_id(message_id)

		if not message or message.user_id != user_id:
			return False

		# 2. Physically remove the file from permanent storage
		if message.file_path:
			await self.file_repo.delete(message.file_path, is_temp = False)

		# 3. Remove the metadata record (or mark as is_deleted=True for soft delete)
		deleted_size = await self.message_repo.delete_message(message_id)
		return deleted_size is not None
