class ServiceError(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)


class UserAuthenticationError(ServiceError):
	"""User authentication failed, for example, incorrect username or password."""

	def __init__(self, message: str = 'Incorrect username or password.'):
		super().__init__(message)


class UserNotVerifiedError(ServiceError):
	"""The user was not verified via email and was unable to perform the operation."""

	def __init__(self, message: str = 'User is not verified. Please check your email.'):
		super().__init__(message)


class MessageNotFoundError(ServiceError):
	"""The message was not found in the database."""

	def __init__(self, message: str = 'Message not found.'):
		super().__init__(message)


class QuotaExceededError(ServiceError):
	"""The quota was exceeded."""

	def __init__(self, message: str = 'Quota exceeded.'):
		super().__init__(message)


class FilePathNotFoundError(ServiceError):
	"""The file was not found in the database."""

	def __init__(self, message: str = 'File not found.'):
		super().__init__(message)


class MessagePermissionError(ServiceError):
	"""Permission denied."""

	def __init__(self, message: str = 'Permission denied.'):
		super().__init__(message)


class FileUploadAbortedError(ServiceError):
	"""The file was uploaded was aborted."""

	def __init__(self, message: str = 'File upload aborted by user.'):
		super().__init__(message)


class UserConstraintError(ServiceError):
	"""The User already verified."""

	def __init__(self, message: str = 'User already verified.'):
		super().__init__(message)


class RateLimitError(ServiceError):
	"""Rate limit exceeded."""

	def __init__(self, message: str = 'Rate limit exceeded.'):
		super().__init__(message)


class OtpInvalidError(ServiceError):
	"""The OTP is invalid."""

	def __init__(self, message: str = 'OTP is invalid.'):
		super().__init__(message)


class OtpLockedError(ServiceError):
	"""The OTP is locked."""

	def __init__(self, message: str = 'OTP is locked.'):
		super().__init__(message)


class EmailDeliveryError(ServiceError):
	"""Email delivery failed."""

	def __init__(self, message: str = 'Email delivery failed.'):
		super().__init__(message)
