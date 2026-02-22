from typing import Optional

from redis import asyncio as aioredis

from app.core.settings import settings


# tackle with the repo of deleting
class RedisRepo:
	def __init__(self, redis_url: str):
		self.client = aioredis.from_url(redis_url, decode_responses = True)
		self._auth_prefix = "auth:otp"

	# --- Message TTL ---
	async def set_message_ttl(self, message_id: int, expire_sec: int = settings.MESSAGE_TTL_SECONDS):
		key = f"msg_ttl:{message_id}"
		await self.client.set(key, "active", expire_sec)

	async def delete_timer(self, message_id: int):
		key = f"msg_ttl:{message_id}"
		await self.client.delete(key)

	# --- Auth (OTP) ---
	async def set_otp(self, username: str, otp_code: str, ex: int = settings.OTP_EXPIRATION_SECONDS):
		key = f"{self._auth_prefix}:{username}"
		await self.client.set(key, otp_code, ex)

	async def get_otp(self, username: str) -> Optional[str]:
		key = f"{self._auth_prefix}:{username}"
		return await self.client.get(key)

	async def delete_otp(self, username: str):
		key = f"{self._auth_prefix}:{username}"
		await self.client.delete(key)
