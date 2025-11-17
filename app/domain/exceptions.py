# ----------------------------------------------------------------------
# 1.Base Exception
# ----------------------------------------------------------------------
class DomainException(Exception):
	"""Base domain exception class"""

	def __init__(self, message: str = "A domain-level business error occurred."):
		super().__init__(message)
		self.message = message


# ----------------------------------------------------------------------
# 2.Storage/Quota Errors
# ----------------------------------------------------------------------
class FileMetadataNotFoundError(DomainException):
	"""The requested file metadata does not exist in the database."""

	def __init__(self, file_id: int):
		super().__init__(f"File with ID {file_id} not found in metadata.")


class FileQuotaExceededError(DomainException):
	"""The user uploaded files exceeding the maximum quota limit."""

	def __init__(self, user_id: int, current_size: int, max_size: int):
		super().__init__(f"User {user_id} upload quota exceeded. Used: {current_size} / Max: {max_size}.")


# ----------------------------------------------------------------------
# 3.Authorization/Permission Errors
# ----------------------------------------------------------------------
class NotAuthorizedError(DomainException):
	"""The user attempts to delete or access files that do not belong to them."""

	def __init__(self, user_id: int, file_id: int):
		super().__init__(f"User {user_id} is not authorized to access file {file_id}.")


class UserNotActiveError(DomainException):
	"""The user account is not activated."""

	def __init__(self, user_id: int):
		super().__init__(f"User {user_id} account is not active.")
