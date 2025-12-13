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
