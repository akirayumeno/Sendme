from pathlib import Path
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.router import router as message_router
from app.core.dependencies import (
	get_current_user_id,
	get_file_repo,
	get_file_service,
	get_message_service,
)
from app.storage.file_repo import FileRepo


def _msg_payload(msg_id: int, msg_type: str = "text") -> dict:
	now = datetime.now(timezone.utc).isoformat()
	return {
		"id": msg_id,
		"type": msg_type,
		"status": "SENT",
		"content": "hello" if msg_type == "text" else None,
		"created_at": now,
		"updated_at": now,
		"device": "desktop",
	}


def test_send_text_and_history():
	message_service = AsyncMock()
	file_service = AsyncMock()
	with TemporaryDirectory() as tmp:
		file_repo = FileRepo(upload_dir=Path(tmp))

		message_service.create_text_message.return_value = _msg_payload(1)
		message_service.get_history.return_value = [_msg_payload(1)]

		app = FastAPI()
		app.include_router(message_router, prefix="/api/v1")
		app.dependency_overrides[get_current_user_id] = lambda: 1
		app.dependency_overrides[get_message_service] = lambda: message_service
		app.dependency_overrides[get_file_service] = lambda: file_service
		app.dependency_overrides[get_file_repo] = lambda: file_repo
		client = TestClient(app)

		resp = client.post("/api/v1/messages/text", json={"content": "hello", "device": "desktop"})
		assert resp.status_code == 200
		assert resp.json()["id"] == 1

		history = client.get("/api/v1/messages/history")
		assert history.status_code == 200
		assert len(history.json()) == 1



def test_upload_download_view():
	message_service = AsyncMock()
	file_service = AsyncMock()
	with TemporaryDirectory() as tmp:
		file_repo = FileRepo(upload_dir=Path(tmp))
		user_dir = file_repo.upload_dir / "1"
		user_dir.mkdir(parents=True, exist_ok=True)
		target = user_dir / "demo.txt"
		target.write_text("demo")

		file_service.handle_initial_upload.return_value = {
			"temp_filename": "tmp.bin",
			"original_filename": "demo.txt",
			"size_bytes": 4,
			"mime_type": "text/plain",
		}
		file_service.finalize_file_message.return_value = _msg_payload(2, msg_type="file")
		file_service.get_file_path_for_user.return_value = "1/demo.txt"
		file_service.get_file_for_user.return_value = type(
			"FileMessage",
			(),
			{"type": "file", "file_path": "1/demo.txt", "user_id": 1},
		)()

		app = FastAPI()
		app.include_router(message_router, prefix="/api/v1")
		app.dependency_overrides[get_current_user_id] = lambda: 1
		app.dependency_overrides[get_message_service] = lambda: message_service
		app.dependency_overrides[get_file_service] = lambda: file_service
		app.dependency_overrides[get_file_repo] = lambda: file_repo
		client = TestClient(app)

		upload = client.post(
			"/api/v1/messages/upload",
			files={"file": ("demo.txt", b"demo", "text/plain")},
			data={"device": "desktop"},
		)
		assert upload.status_code == 200

		download = client.get("/api/v1/messages/2/download")
		assert download.status_code == 200
		assert download.content == b"demo"

		view = client.get("/api/v1/messages/2/view")
		assert view.status_code == 415
