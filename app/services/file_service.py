import uuid
from pathlib import Path
from typing import Any

from app.core.exceptions import FileMetadataNotFoundError
from app.domain.models import File
from app.storage.abstract_storage_repo import AbstractStorageRepo


class FileService:
	def __init__(self, storage_repo: AbstractStorageRepo, metadata_repo: Any):
		self.storage_repo = storage_repo
		self.metadata_repo = metadata_repo

	async def upload_file(self, file_data: bytes, original_name: str, user_id: int) -> dict:
		"""Upload file to local storage"""
		file_size = len(file_data)
		# Business rule check
		await self.metadata_repo.check_quota(user_id, file_size)

		# Generate a unique storage key
		file_ext = Path(original_name).suffix
		file_path = f"{uuid.uuid4()}.{file_ext}"

		# Store file content
		bytes_stored = await self.storage_repo.save(file_data, file_path)

		# renew the database data
		metadata = await self.metadata_repo.create_file_metadata(
			user_id = user_id,
			file_path = file_path,
			file_size = bytes_stored,
			original_name = original_name
		)

		return {
			"file_path":file_path,
			"file_size":bytes_stored,
			"original_name":original_name,
			"file_id":metadata.file_id,
		}

	async def download_file(self, file_id, file_path, user_id) -> bool:
		"""Download a file from local storage"""
		try:
			address = await self.metadata_repo.get_file_metadata_by_id(file_id)
		except FileMetadataNotFoundError:
			return False
		File.check_download_permission(user_id)
		try:
			content = await self.storage_repo.load(file_path)
		except StorageContentError:
			return False
		return True
