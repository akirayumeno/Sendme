from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.services.notification_service import NotificationService


@pytest.fixture
def notification_service():
	"""Fixture to initialize the notification service instance for testing."""
	return NotificationService()


@pytest.mark.asyncio
async def test_send_verification_mail_logic(notification_service):
	"""
	Test that send_verification_mail correctly renders the template
	and passes the right arguments to the SMTP 'send' function.
	"""
	# 1. Define test data
	test_recipient = "user@example.com"
	test_username = "test_user"
	test_code = "123456"

	# 2. Patch 'send' from aiosmtplib.
	# We use AsyncMock because 'send' is a coroutine (async function).
	with patch("app.services.notification_service.send", new_callable = AsyncMock) as mock_send:
		# 3. Patch the Jinja2 template loader ('load') to avoid reading real files from disk.
		with patch("app.services.notification_service.load.get_template") as mock_get_template:
			# Create a mock template and define its render behavior
			mock_template = MagicMock()
			mock_template.render.return_value = "<html>Mocked Email Body</html>"
			mock_get_template.return_value = mock_template

			# --- Execute the method under test ---
			await notification_service.send_verification_mail(
				test_recipient,
				test_username,
				test_code
			)

			# --- Verification / Assertions ---

			# Ensure the SMTP send function was called exactly once
			mock_send.assert_called_once()

			# Inspect the first positional argument passed to 'send' (the EmailMessage object)
			# call_args[0][0] retrieves the first argument of the first call
			sent_message = mock_send.call_args[0][0]

			# Use standard assertions to avoid 'Unresolved reference' errors
			assert sent_message["To"] == test_recipient
			assert sent_message["Subject"] == "Your Verification Code"
			assert "Sendme Support" in sent_message["From"]

			# Inspect the keyword arguments (SMTP configuration)
			# call_args[1] retrieves a dictionary of the keyword arguments passed to 'send'
			kwargs = mock_send.call_args[1]
			assert kwargs["hostname"] == notification_service.smtp_server
			assert kwargs["port"] == notification_service.smtp_port
			assert kwargs["username"] == notification_service.email
			assert kwargs["password"] == notification_service.code
