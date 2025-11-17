from pathlib import Path
from typing import Optional

import aiofiles


class LocalStorageRepo:
	"""Implementation of local disk storage."""

	# Initialization: Define the root storage directory
	def __init__(self, upload_dir: Path = Path("local_storage")):
		"""Initialization."""
		self.upload_dir = upload_dir
		self.upload_dir.mkdir(parents = True, exist_ok = True)

	# Implement the SAVE interface
	async def save(self, content: bytes, file_path: str) -> int:
		"""Save a file/image message."""
		full_path = self.upload_dir / file_path

		async with aiofiles.open(full_path, "wb") as f:
			await f.write(content)

		return len(content)

	# Implement the LOAD interface
	async def load(self, file_path: str) -> Optional[bytes]:
		"""Load a file/image message."""
		full_path = self.upload_dir / file_path
		if not full_path.exists():
			return None

		async with aiofiles.open(full_path, "rb") as f:
			return await f.read()

	# Implement the DELETE interface
	async def delete(self, file_path: str) -> bool:
		"""Delete a file/image message."""
		full_path = self.upload_dir / file_path
		if full_path.exists():
			try:
				full_path.unlink()
				return True
			except OSError:
				return False
		# When file is not existed, also regard it as deleted.
		return True
