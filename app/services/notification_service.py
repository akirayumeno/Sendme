import os
from email.message import EmailMessage

from aiosmtplib import send
from jinja2 import Environment, FileSystemLoader

from app.core.settings import settings

template_dir = os.path.join(os.path.dirname(__file__), "../templates")
load = Environment(loader = FileSystemLoader(template_dir))


class NotificationService:
	def __init__(self):
		self.smtp_server = settings.SMTP_SERVER
		self.smtp_port = settings.SMTP_PORT
		self.email = settings.SMTP_EMAIL
		self.code = settings.SMTP_CODE

	async def send_verification_mail(self, recipient: str, username, code: str):
		"""
		Sends an HTML email with the verification code.
		"""
		template = load.get_template('verification_mail.html')
		html_content = template.render(username = username, code = code)

		message = EmailMessage()
		message['From'] = f'Sendme Support <{self.email}>'
		message['To'] = recipient
		message['Subject'] = 'Your Verification Code'

		message.set_content(html_content, subtype = 'html')
		# send email
		await send(
			message,
			hostname = self.smtp_server,
			port = self.smtp_port,
			username = self.email,
			password = self.code,
			use_tls = (self.smtp_port == 465),
			start_tls = (self.smtp_port == 587)
		)


notification_service = NotificationService()
