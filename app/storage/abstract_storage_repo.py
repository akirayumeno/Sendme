from abc import ABC, abstractmethod


class AbstractFileRepo(ABC):
	"""Abstract storage repository interface."""

	@abstractmethod
	async def save(self, file_stream, file_path: str, is_temp: bool = True) -> int:
		"""Save a file/image message."""
		raise NotImplementedError

	@abstractmethod
	async def move_to_final(self, temp_filename: str, final_filename: str) -> int:
		"""Load a file/image message."""
		raise NotImplementedError

	@abstractmethod
	async def delete(self, file_path: str, is_temp: bool = False) -> int:
		"""Delete a file/image message."""
		raise NotImplementedError

	@abstractmethod
	async def delete_temp(self, temp_filename: str) -> bool:
		"""Delete a file/image message."""
		raise NotImplementedError
