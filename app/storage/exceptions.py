class RepositoryError(Exception):
	def __init__(self, message: str):
		self.message = message


class UserNotFoundErrorById(RepositoryError):
	def __init__(self, user_id):
		super().__init__(f"User {user_id} Not found in the database.")
		self.user_id = user_id


class UserNotFoundErrorByName(RepositoryError):
	def __init__(self, username):
		super().__init__(f"User {username} Not found in the database.")
		self.username = username


class UserConstraintError(RepositoryError):
	"""Data constraint violation error."""

	def __init__(self, message: str, field: str = None, value: str = None):
		self.field = field  # (e.g., 'username')
		self.value = value  # (e.g., 'testuser')
		self.message = message

		super().__init__(f"Data constraint violation: {message}")


class MessageNotFoundError(RepositoryError):
	"""Requested message record not found."""

	def __init__(self, message_id):
		super().__init__(f"Message {message_id} Not found in the database.")


class MessageUpdateError(RepositoryError):
	"""Failed to update message."""

	def __init__(self, message_id):
		super().__init__(f"Error updating message {message_id}.")


class MessageRestoreError(RepositoryError):
	"""Failed in Restoring message record."""

	def __init__(self, message_id):
		super().__init__(f"Error restoring message {message_id}.")


class FileWriteError(RepositoryError):
	"""File write failure."""

	def __init__(self, file_path: str, original_exception: Exception = None):
		message = f"Failed to write file to storage at path: {file_path}."
		if original_exception:
			message += f" Original error: {original_exception.__class__.__name__}"

		super().__init__(message)
		self.file_path = file_path


class FileLoadError(RepositoryError):
	"""File load failure."""

	def __init__(self, file_path: str, original_exception: Exception = None):
		message = f"Failed to load file from storage at path: {file_path}."
		if original_exception:
			message += f" Original error: {original_exception.__class__.__name__}"

		super().__init__(message)
		self.file_path = file_path


class FileDeleteError(RepositoryError):
	"""File read failure."""

	def __init__(self, file_path: str, original_exception: Exception = None):
		message = f"Failed to delete file from storage at path: {file_path}. The file may still exist."
		if original_exception:
			message += f" Original error: {original_exception.__class__.__name__}"

		super().__init__(message)
		self.file_path = file_path
