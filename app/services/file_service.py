import uuid

from fastapi import UploadFile

from app.core.enums import MessageStatus
from app.core.orm_models import Message
from app.core.settings import settings
from app.schemas.schemas import FileMessageCreate
from app.services.exceptions import QuotaExceededError, FilePathNotFoundError, MessageNotFoundError, \
	MessagePermissionError, FileUploadAbortedError
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

	async def handle_initial_upload(self, file: UploadFile) -> dict:
		"""
		Stage 1: Save the incoming stream to a temporary directory.
		This allows for file validation and 'Cancel' functionality before
		the message is officially created in the database.
		"""
		# Generate a unique temporary name to prevent collision
		temp_filename = f"{uuid.uuid4()}_{file.filename}"

		# Stream the file to the temp folder via Repo
		# If the connection is aborted, FileRepo handles the cleanup internally
		try:
			size_bytes = await self.file_repo.save(file.file, temp_filename, is_temp = True)
		except Exception as e:
			raise FileUploadAbortedError() from e

		return {
			"temp_filename":temp_filename,
			"original_filename":file.filename,
			"size_bytes":size_bytes,
			"mime_type":file.content_type
		}

	async def finalize_file_message(
			self,
			schema: FileMessageCreate,
			temp_filename: str,
			file_size: int
	) -> Message:
		# 1. Physical existence check
		temp_path = self.file_repo.temp_dir / temp_filename
		if not temp_path.exists():
			raise FilePathNotFoundError(f"Temporary file {temp_filename} not found.")

		# 2. Logic & Safety Check (The method you extracted)
		await self._check_quota(schema.user_id, temp_filename, file_size)

		# 3. Physical Move: Temp -> Final
		# Using the path from schema (populated by handle_initial_upload or controller)
		await self.file_repo.move_to_final(temp_filename, schema.file_path)

		# 4. Database Persistence
		# schema.model_dump() already contains the finalized file_path and metadata
		data = schema.model_dump()
		data["status"] = MessageStatus.sent
		uploaded_messages = await self.message_repo.create_message(data)

		# 5. Calculate capacity
		await self.user_repo.update_used_capacity(schema.user_id, file_size)

		return uploaded_messages

	async def cancel_pending_upload(self, temp_filename: str):
		"""
		Action: Explicitly remove a file from temp storage if the user
		clicks 'X' on the UI before sending the message.
		"""
		return await self.file_repo.delete_temp(temp_filename)

	async def delete_existing_file(self, message_id: int, user_id: int) -> int:
		"""
		Action: Permanent deletion.
		Removes both the physical file from disk and the record from the database.
		Includes owner validation to prevent unauthorized deletion.
		"""
		# 1. Fetch metadata to get the file path
		message = await self.message_repo.get_by_message_id(message_id)

		if not message:
			raise MessageNotFoundError("Message not found.")
		if message.user_id != user_id:
			raise MessagePermissionError("Message Permission denied.")

		# 2. Remove the metadata record
		released_bytes = await self.message_repo.delete_message(message_id)
		# 3. Refresh capacity
		used_quota_bytes = await self.user_repo.update_used_capacity(user_id, released_bytes)

		# 4. Physically remove the file from permanent storage
		if message.file_path:
			await self.file_repo.delete(message.file_path, is_temp = False)
		else:
			raise FilePathNotFoundError("File was not found in the message.")
		return used_quota_bytes

	async def _check_quota(self, user_id: int, temp_filename: str, file_size: int):
		"""
		Internal helper to verify user quota before finalizing.
		Raises UserQuotaExceededError and cleans up temp file if check fails.
		"""

		current_used = await self.user_repo.get_used_capacity(user_id)

		if current_used + file_size > settings.DEFAULT_MAX_CAPACITY_BYTES:
			# Cleanup: Don't leave garbage in temp if we're going to reject it
			await self.file_repo.delete_temp(temp_filename)
			raise QuotaExceededError(
				f"Quota exceeded. Available: {settings.DEFAULT_MAX_CAPACITY_BYTES - current_used} bytes, "
				f"Requested: {file_size} bytes."
			)

	async def get_file_path_for_user(self, message_id: int, user_id: int) -> str:
		message = await self.message_repo.get_by_message_id(message_id)

		if message.user_id != user_id:
			raise MessagePermissionError("Message Permission denied.")
		if not message.file_path:
			raise FilePathNotFoundError("File was not found in the message.")
		return message.file_path
