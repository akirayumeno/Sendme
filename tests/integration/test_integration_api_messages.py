from pathlib import Path
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.router import router as message_router
from app.core.dependencies import (
	get_current_user_id,
	get_file_repo,
	get_file_service,
	get_message_service,
)
from app.schemas.schemas import TextMessageCreate
from app.storage.file_repo import FileRepo


class FakeMessageService:
	def __init__(self):
		self.messages = []
		self.seq = 1

	async def create_text_message(self, schema: TextMessageCreate):
		now = datetime.now(timezone.utc).isoformat()
		msg = {
			"id": str(self.seq),
			"type": "text",
			"status": "SENT",
			"content": schema.content,
			"created_at": now,
			"updated_at": now,
			"device": schema.device.value,
		}
		self.seq += 1
		self.messages.append(msg)
		return msg

	async def get_history(self, user_id: int, page: int = 1):
		return list(reversed(self.messages))

	async def delete_message(self, message_id: int, user_id: int):
		return True


class FakeFileService:
	def __init__(self, root: str):
		self.root = root

	async def handle_initial_upload(self, file):
		data = await file.read()
		path = f"1/{file.filename}"
		with open(f"{self.root}/{path}", "wb") as f:
			f.write(data)
		return {
			"temp_filename": "unused",
			"original_filename": file.filename,
			"size_bytes": len(data),
			"mime_type": file.content_type,
		}

	async def finalize_file_message(self, schema, temp_filename: str, file_size: int):
		now = datetime.now(timezone.utc).isoformat()
		return {
			"id": "99",
			"type": "file",
			"status": "SENT",
			"filePath": schema.file_path,
			"fileName": schema.file_name,
			"fileType": schema.file_type,
			"fileSize": file_size,
			"created_at": now,
			"updated_at": now,
			"device": schema.device.value,
		}

	async def get_file_path_for_user(self, message_id: int, user_id: int):
		return "1/demo.txt"

	async def get_file_for_user(self, message_id: int, user_id: int):
		return SimpleNamespace(type = "image", file_path = "1/demo.txt", user_id = user_id)


def test_message_api_flow_end_to_end():
	with TemporaryDirectory() as tmp:
		file_repo = FileRepo(upload_dir=Path(tmp))
		(file_repo.upload_dir / "1").mkdir(parents=True, exist_ok=True)
		(file_repo.upload_dir / "1" / "demo.txt").write_text("demo")

		app = FastAPI()
		app.include_router(message_router, prefix="/api/v1")
		app.dependency_overrides[get_current_user_id] = lambda: 1
		app.dependency_overrides[get_message_service] = lambda: FakeMessageService()
		app.dependency_overrides[get_file_service] = lambda: FakeFileService(tmp)
		app.dependency_overrides[get_file_repo] = lambda: file_repo

		client = TestClient(app)

		send = client.post("/api/v1/messages/text", json={"content": "hello", "device": "desktop"})
		assert send.status_code == 200
		assert send.json()["content"] == "hello"

		history = client.get("/api/v1/messages/history")
		assert history.status_code == 200

		download = client.get("/api/v1/messages/99/download")
		assert download.status_code == 200
		assert download.content == b"demo"

		view = client.get("/api/v1/messages/99/view")
		assert view.status_code == 200
		assert view.content == b"demo"
