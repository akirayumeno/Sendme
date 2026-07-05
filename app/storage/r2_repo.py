import asyncio
import os
from pathlib import Path

import aiofiles
import aiofiles.os as aios
import boto3

from app.core.settings import settings
from app.storage.exceptions import CapacityExceededError, FileDeleteError, FileWriteError, RepositoryError


class R2FileRepo:
	def __init__(
			self,
			upload_dir: Path,
			endpoint: str,
			bucket: str,
			access_key_id: str,
			secret_access_key: str,
	):
		self.upload_dir = upload_dir
		self.temp_dir = self.upload_dir / "temp"
		self.upload_dir.mkdir(parents = True, exist_ok = True)
		self.temp_dir.mkdir(parents = True, exist_ok = True)
		self.bucket = bucket
		self.client = boto3.client(
			"s3",
			endpoint_url = endpoint,
			aws_access_key_id = access_key_id,
			aws_secret_access_key = secret_access_key,
			region_name = "auto",
		)

	async def save(self, file_stream, file_path: str, is_temp: bool = True) -> int:
		base = self.temp_dir if is_temp else self.upload_dir
		full_path = base / file_path
		full_path.parent.mkdir(parents = True, exist_ok = True)
		bytes_written = 0
		chunk_size = 1024 * 1024

		try:
			async with aiofiles.open(full_path, "wb") as f:
				if hasattr(file_stream, "__aiter__"):
					async for chunk in file_stream:
						bytes_written = await self._write_chunk(f, chunk, bytes_written)
				elif hasattr(file_stream, "read") and asyncio.iscoroutinefunction(file_stream.read):
					while True:
						chunk = await file_stream.read(chunk_size)
						if not chunk:
							break
						bytes_written = await self._write_chunk(f, chunk, bytes_written)
				elif hasattr(file_stream, "read"):
					while True:
						chunk = await asyncio.to_thread(file_stream.read, chunk_size)
						if not chunk:
							break
						bytes_written = await self._write_chunk(f, chunk, bytes_written)
				else:
					raise TypeError(f"Unsupported file stream type: {type(file_stream)!r}")
			return bytes_written
		except CapacityExceededError:
			if await aios.path.exists(full_path):
				await aios.remove(full_path)
			raise
		except Exception as e:
			if await aios.path.exists(full_path):
				await aios.remove(full_path)
			raise FileWriteError(file_path = str(full_path), original_exception = e) from e

	async def _write_chunk(self, file_handle, chunk: bytes, bytes_written: int) -> int:
		if not chunk:
			return bytes_written
		if bytes_written + len(chunk) > settings.MAX_FILE_SIZE_BYTES:
			raise CapacityExceededError("File size limit reached during stream.")
		await file_handle.write(chunk)
		return bytes_written + len(chunk)

	async def move_to_final(self, temp_filename: str, final_filename: str) -> str:
		temp_path = self.temp_dir / temp_filename
		if not temp_path.exists():
			raise RepositoryError(f"Temporary file missing: {temp_filename}")

		try:
			await asyncio.to_thread(
				self.client.upload_file,
				str(temp_path),
				self.bucket,
				final_filename,
			)
			await aios.remove(temp_path)
			return str(final_filename)
		except Exception as e:
			raise RepositoryError(f"R2 upload failed: {e}") from e

	async def delete(self, file_path: str, is_temp: bool = False) -> bool:
		if is_temp:
			full_path = self.temp_dir / file_path
			try:
				if full_path.exists():
					await aios.remove(full_path)
					return True
				return False
			except Exception as e:
				raise FileDeleteError(str(full_path), e) from e

		try:
			await asyncio.to_thread(self.client.delete_object, Bucket = self.bucket, Key = file_path)
			return True
		except Exception as e:
			raise FileDeleteError(file_path, e) from e

	async def delete_temp(self, temp_filename: str) -> bool:
		return await self.delete(temp_filename, is_temp = True)

	async def get_presigned_url(self, file_path: str, as_download: bool) -> str:
		params = {"Bucket": self.bucket, "Key": file_path}
		if as_download:
			params["ResponseContentDisposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
		return await asyncio.to_thread(
			self.client.generate_presigned_url,
			"get_object",
			Params = params,
			ExpiresIn = settings.R2_SIGNED_URL_EXPIRE_SECONDS,
		)

	async def get_file_response_data(self, file_path: str) -> tuple[bytes, str | None]:
		def _load_object():
			response = self.client.get_object(Bucket = self.bucket, Key = file_path)
			return response["Body"].read(), response.get("ContentType")

		return await asyncio.to_thread(_load_object)
