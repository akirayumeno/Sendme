from pathlib import Path
from typing import Optional

import aiofiles
import aiofiles.os as aios

from app.storage.exceptions import FileWriteError, FileLoadError, FileDeleteError, RepositoryError


# Unstructured data (Content): The actual binary file content (such as the byte stream of images, videos, and documents).
# Large blocks of asynchronous I/O (requires async/await support).
# Local disk file system, S3 storage API
class FileRepo:
	"""Implementation of local disk storage."""

	# Initialization: Define the root storage directory
	def __init__(self, upload_dir: Path = Path("local_files")):
		"""Initialization."""
		self.upload_dir = upload_dir
		self.upload_dir.mkdir(parents = True, exist_ok = True)

	# Implement the SAVE interface
	async def save(self, file_stream, file_path: str) -> int | None:
		"""Saves file content using streaming/chunked write."""
		full_path = self.upload_dir / file_path
		bytes_written = 0
		try:
			async with aiofiles.open(full_path, "wb") as f:
				async for chunk in file_stream:
					await f.write(chunk)
					bytes_written += len(chunk)
				return bytes_written
		except Exception as e:
			raise FileWriteError(file_path = file_path, original_exception = e) from e

	# Implement the LOAD interface
	async def load(self, file_path: str) -> Optional[bytes]:
		"""Load a file/image message."""
		full_path = self.upload_dir / file_path
		if not await aios.path.exists(full_path):
			raise FileLoadError(file_path = file_path, original_exception = FileNotFoundError("File not found"))
		try:
			async with aiofiles.open(full_path, "rb") as f:
				return await f.read()
		except Exception as e:
			raise FileLoadError(file_path = file_path, original_exception = e) from e

	# Implement the DELETE interface
	async def delete(self, file_path: str) -> bool:
		"""Delete a file/image message."""
		full_path = self.upload_dir / file_path

		if full_path.exists():
			try:
				await aios.remove(full_path)
				return True
			except Exception as e:
				raise FileDeleteError(file_path = file_path, original_exception = e) from e
		# When file is not existed, also regard it as deleted.
		return True

	async def get_file_size(self, file_path: str) -> Optional[int]:
		"""Returns the size of the file in bytes."""
		full_path: Path = self.upload_dir / file_path
		if not await aios.path.exists(full_path):
			return None
		try:
			size = await aios.path.getsize(full_path)
			return size

		except Exception as e:
			raise FileLoadError(file_path = file_path, original_exception = e) from e

	async def move_file(self, temp_file_path: str, final_file_path: str) -> bool:
		"""Move the file atomically from the temporary directory to the permanent directory."""
		temp_full_path = self.upload_dir / temp_file_path
		final_full_path = self.upload_dir / final_file_path

		if not await aios.path.exists(temp_full_path):
			raise FileLoadError(
				file_path = temp_file_path, original_exception = FileNotFoundError("Temp file not found")
			)

		try:
			await aios.rename(temp_full_path, final_full_path)
			return True
		except Exception as e:
			raise RepositoryError(f"Failed to move file from {temp_file_path} to {final_file_path}") from e
