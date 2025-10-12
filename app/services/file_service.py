from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
import aiofiles
import uuid
from pathlib import Path

class FileService:
	def __init__(self, upload_dir: str = "uploads"):
		self.upload_dir = Path(upload_dir)
		self.upload_dir.mkdir(exist_ok=True)

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
				"path": unique_filename,
				"size": len(content),
				"original_name": file.filename
			}
		except Exception as e:
			raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

	async def get_file(self, file_path: str):
		"""Serve file from storage"""
		full_path = self.upload_dir / file_path
		if not full_path.exists():
			raise HTTPException(status_code=404, detail="File not found")

		return FileResponse(full_path)