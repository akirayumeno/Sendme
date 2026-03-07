import logging;
from pathlib import Path

import aiofiles
import aiofiles.os as aios

from app.core.settings import settings
from app.storage.exceptions import FileWriteError, RepositoryError, FileDeleteError, CapacityExceededError

logger = logging.getLogger(__name__)


class FileRepo:
	def __init__(self, upload_dir: Path = Path("local_files")):
		# place for all the files
		self.upload_dir = upload_dir
		# Create both main and temp directories
		self.temp_dir = self.upload_dir / "temp"
		self.upload_dir.mkdir(parents = True, exist_ok = True)
		self.temp_dir.mkdir(parents = True, exist_ok = True)

	async def save(self, file_stream, file_path: str, is_temp: bool = True) -> int:
		"""
		Saves file content.
		If is_temp=True, it saves to the 'temp' folder for safety during upload.
		"""
		# Determine base directory
		base = self.temp_dir if is_temp else self.upload_dir
		full_path = base / file_path

		# Ensure subdirectories exist (e.g., if file_path is 'user1/image.png')
		full_path.parent.mkdir(parents = True, exist_ok = True)

		bytes_written = 0
		try:
			async with aiofiles.open(full_path, "wb") as f:
				async for chunk in file_stream:
					if bytes_written + len(chunk) > settings.DEFAULT_MAX_CAPACITY_BYTES:
						raise CapacityExceededError("Disk or User limit reached during stream.")
					await f.write(chunk)
					bytes_written += len(chunk)
			return bytes_written
		except Exception as e:
			# Clean up partial file on failure (Cancel logic)
			if await aios.path.exists(full_path):
				await aios.remove(full_path)
				logger.warning(f"File upload aborted by user. Cleaned up partial file: {file_path}")
			raise FileWriteError(file_path = str(full_path), original_exception = e) from e

	async def move_to_final(self, temp_filename: str, final_filename: str) -> str:
		"""
		Moves a file from temp to final destination.
		Returns the relative path for database storage.
		"""
		temp_path = self.temp_dir / temp_filename
		final_path = self.upload_dir / final_filename

		final_path.parent.mkdir(parents = True, exist_ok = True)

		try:
			# move the file from temp to final destination
			await aios.rename(temp_path, final_path)
			return str(final_filename)
		except Exception as e:
			raise RepositoryError(f"Atomic move failed: {e}") from e

	async def delete(self, file_path: str, is_temp: bool = False) -> bool:
		"""
		Physically delete a file from the disk.
		:param file_path: Relative path to the file.
		:param is_temp: If True, look in the temp directory.
		"""
		base = self.temp_dir if is_temp else self.upload_dir
		full_path = base / file_path

		try:
			if full_path.exists():
				await aios.remove(full_path)
				return True
			return False
		except Exception as e:
			raise FileDeleteError(f"Failed to delete file {full_path}: {e}") from e

	async def delete_temp(self, temp_filename: str) -> bool:
		"""Specific helper to delete from temp folder when it's uploaded but not message out."""
		return await self.delete(temp_filename, is_temp = True)
