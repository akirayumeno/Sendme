import time
from typing import Optional

from redis import asyncio as aioredis

from app.core.settings import settings


def _otp_key(email: str) -> str:
	return f"auth:otp:{email}"


def _cooldown_key(email: str) -> str:
	return f"auth:otp:cooldown:{email}"


def _attempt_key(email: str) -> str:
	return f"auth:otp:attempts:{email}"


def _lock_key(email: str) -> str:
	return f"auth:otp:lock:{email}"


class RedisRepo:
	def __init__(self, redis_url: str):
		self.client = aioredis.from_url(redis_url, decode_responses = True)
		self._ttl_index_key = "msg_ttl:index"

	# --- Message TTL ---
	async def set_message_ttl(self, message_id: int, expire_sec: int = settings.MESSAGE_TTL_SECONDS):
		key = f"msg_ttl:{message_id}"
		expire_at = int(time.time()) + expire_sec
		async with self.client.pipeline(transaction = True) as pipe:
			await pipe.set(key, "active", ex = expire_sec)
			await pipe.zadd(self._ttl_index_key, {str(message_id): expire_at})
			await pipe.execute()

	async def delete_timer(self, message_id: int):
		key = f"msg_ttl:{message_id}"
		async with self.client.pipeline(transaction = True) as pipe:
			await pipe.delete(key)
			await pipe.zrem(self._ttl_index_key, str(message_id))
			await pipe.execute()

	async def get_expired_message_ids(self, limit: int = 100) -> list[int]:
		now_ts = int(time.time())
		raw_ids = await self.client.zrangebyscore(
			self._ttl_index_key,
			min = "-inf",
			max = now_ts,
			start = 0,
			num = limit,
		)
		return [int(v) for v in raw_ids]

	# --- Auth (OTP) ---
	async def set_otp(self, mail: str, otp_code: str, ex: int = settings.OTP_EXPIRATION_SECONDS):
		await self.client.set(_otp_key(mail), otp_code, ex)

	async def get_otp(self, mail: str) -> Optional[str]:
		return await self.client.get(_otp_key(mail))

	# Control the retransmission frequency
	async def set_otp_cooldown(self, email: str, ex: int):
		await self.client.set(_cooldown_key(email), "1", ex = ex)

	async def has_otp_cooldown(self, email: str) -> bool:
		return await self.client.exists(_cooldown_key(email)) == 1

	# Count the number of incorrect entries
	async def incr_otp_attempts(self, email: str, ex: int) -> int:
		key = _attempt_key(email)
		n = await self.client.incr(key)
		if n == 1:
			await self.client.expire(key, ex)
		return n

	async def clear_otp_attempts(self, email: str):
		await self.client.delete(_attempt_key(email))

	# Temporarily locked after reaching the limit
	async def lock_otp(self, email: str, ex: int):
		await self.client.set(_lock_key(email), "1", ex = ex)

	async def is_otp_locked(self, email: str) -> bool:
		return await self.client.exists(_lock_key(email)) == 1

	async def clear_otp_state(self, email: str):
		await self.client.delete(
			_otp_key(email),
			_attempt_key(email),
			_cooldown_key(email),
		)
