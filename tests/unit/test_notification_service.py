from unittest.mock import patch, MagicMock

import pytest

from app.services.exceptions import EmailDeliveryError
from app.services.notification_service import NotificationService


@pytest.fixture
def notification_service():
	"""
	Fixture to initialize the notification service instance for testing.
	"""
	return NotificationService()


@pytest.mark.asyncio
async def test_send_verification_mail_resend_logic(notification_service):
	"""
	Test that send_verification_mail correctly renders the Jinja2 template
	and passes the expected payload to the Resend API SDK.
	"""
	# 1. Define test data
	test_recipient = "user@example.com"
	test_username = "test_user"
	test_code = "123456"

	# 2. Patch the Resend SDK's send method.
	# Since we use asyncio.to_thread in the service, we mock the underlying synchronous call.
	with patch("resend.Emails.send") as mock_resend_send:
		# 3. Patch the Jinja2 template loader ('load') to avoid I/O operations during unit tests.
		with patch("app.services.notification_service.load.get_template") as mock_get_template:
			# Create a mock template and define its render behavior
			mock_template = MagicMock()
			mock_template.render.return_value = "<html>Mocked Email Body</html>"
			mock_get_template.return_value = mock_template

			# Simulate a successful API response
			mock_resend_send.return_value = {"id":"test_email_id"}

			# --- Execute the method under test ---
			await notification_service.send_verification_mail(
				test_recipient,
				test_username,
				test_code
			)

			# --- Verification / Assertions ---

			# Ensure the Resend API was called exactly once
			mock_resend_send.assert_called_once()

			# Retrieve the arguments passed to the mock to verify the payload structure
			# resend.Emails.send expects a dictionary of type SendParams
			called_params = mock_resend_send.call_args[0][0]

			# Verify that the recipient is passed as a list (Resend requirement)
			assert called_params["to"] == [test_recipient]
			assert called_params["subject"] == "Your Verification Code"
			assert "<html>Mocked Email Body</html>" in called_params["html"]

			# Ensure the 'from' field contains the verified domain or service name
			assert "onboarding@send-me.dev" in called_params["from"] or "SendMe" in called_params["from"]


@pytest.mark.asyncio
async def test_send_verification_mail_api_failure(notification_service):
	"""
	Test that the service correctly raises a custom EmailDeliveryError
	when the Resend API call fails.
	"""
	# Simulate an unexpected exception from the Resend SDK
	with patch("resend.Emails.send", side_effect = Exception("API Connection Timeout")):
		with patch("app.services.notification_service.load.get_template"):
			with pytest.raises(EmailDeliveryError) as exc_info:
				await notification_service.send_verification_mail(
					"fail@test.com", "user", "000000"
				)

			# Verify the custom error message is passed through
			assert "Failed to deliver verification email" in str(exc_info.value)
