import mimetypes
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse


class FileService:
	def __init__(self, upload_dir: str = "uploads"):
		self.upload_dir = Path(upload_dir)
		self.upload_dir.mkdir(exist_ok = True)

	async def upload_file(self, file: UploadFile) -> dict:
		"""Upload file to local storage"""
		try:
			# Generate unique filename
			file_ext = Path(file.filename).suffix
			unique_filename = f"{uuid.uuid4()}{file_ext}"
			file_path = self.upload_dir / unique_filename

			# Save file
			async with aiofiles.open(file_path, 'wb') as f:
				content = await file.read()
				await f.write(content)

			return {
				"path":unique_filename,
				"size":len(content),
				"original_name":file.filename
			}
		except Exception as e:
			raise HTTPException(status_code = 500, detail = f"File upload failed: {str(e)}")

	async def get_file(self, file_path: str):
		"""Serve file from storage"""
		full_path = self.upload_dir / file_path
		if not full_path.exists():
			raise HTTPException(status_code = 404, detail = "File not found")

		download_filename = full_path.name
		return FileResponse(
			full_path,
			filename = download_filename,
		)

	async def get_image(self, file_path: str):
		"""Serve file from storage"""
		full_path = self.upload_dir / file_path
		if not full_path.exists():
			raise HTTPException(status_code = 404, detail = "File not found")

		mime_type, _ = mimetypes.guess_type(file_path)
		if mime_type is None:
			mime_type = "application/octet-stream"
		if mime_type.startswith("image"):
			return FileResponse(full_path, media_type = mime_type)
		else:
			return FileResponse(
				path = full_path,
				media_type = mime_type,
				filename = full_path.name,
				headers = {"Content-Disposition":f"inline; filename=\"{full_path.name}\""}
			)
