from abc import ABC, abstractmethod


class AbstractFileRepo(ABC):
	"""Abstract storage repository interface."""

	@abstractmethod
	async def save(self, content: bytes, file_path: str) -> int:
		"""Save a file/image message."""
		raise NotImplementedError

	@abstractmethod
	async def load(self, file_path: str) -> int:
		"""Load a file/image message."""
		raise NotImplementedError

	@abstractmethod
	async def delete(self, file_path: str) -> int:
		"""Delete a file/image message."""
		raise NotImplementedError
