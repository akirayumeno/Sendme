from abc import ABC, abstractmethod
from typing import Any, Optional


class AbstractMetadataRepository(ABC):
	"""Abstract metadata repository interface."""

	@abstractmethod
	async def load(
			self, user_id: int, storage_key: str,
			file_size: int, original_name: str
	) -> Any:
		raise NotImplementedError

	@abstractmethod
	async def check_and_update_quota(self, user_id: int, file_size: int) -> bool:
		raise NotImplementedError

	@abstractmethod
	async def mark_file_as_deleted(self, file_id: int, user_id: int) -> bool:
		raise NotImplementedError

	@abstractmethod
	async def get_file_metadata_by_id(self, file_id: int) -> Optional[Any]:
		raise NotImplementedError
