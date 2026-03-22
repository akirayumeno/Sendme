import asyncio
import os
from typing import cast

import resend
from jinja2 import Environment, FileSystemLoader

from app.core.settings import settings
from app.services.exceptions import EmailDeliveryError

template_dir = os.path.join(os.path.dirname(__file__), "../templates")
load = Environment(loader = FileSystemLoader(template_dir))

resend.api_key = settings.RESEND_API_KEY


class NotificationService:
	def __init__(self):
		self.from_email = getattr(settings, "RESEND_FROM_EMAIL", "onboarding@send-me.dev")

	async def send_verification_mail(self, recipient: str, username: str, code: str):
		"""
		Sends an HTML email with the verification code using Resend API.
		"""
		try:
			template = load.get_template('verification_code.html')
			html_content = template.render(username = username, code = code)

			params = {
				"from":f"SendMe <{self.from_email}>",
				"to":[recipient],
				"subject":"Your Verification Code",
				"html":html_content,
			}

			r = await asyncio.to_thread(
				resend.Emails.send,
				cast(resend.Emails.SendParams, params)
			)
			return r
		except Exception as e:
			print(f"Resend Error: {str(e)}")
			raise EmailDeliveryError(f"Failed to deliver verification email: {str(e)}") from e


notification_service = NotificationService()
