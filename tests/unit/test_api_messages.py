from pathlib import Path
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import router as message_router_module
from app.api.router import router as message_router
from app.core import security
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


def test_send_text_and_history(monkeypatch):
	message_service = AsyncMock()
	file_service = AsyncMock()
	ws_broadcast = AsyncMock()
	monkeypatch.setattr(message_router_module.ws_manager, "broadcast_to_user", ws_broadcast)
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
		ws_broadcast.assert_awaited()

		history = client.get("/api/v1/messages/history")
		assert history.status_code == 200
		assert len(history.json()) == 1


def test_upload_download_view(monkeypatch):
	message_service = AsyncMock()
	file_service = AsyncMock()
	ws_broadcast = AsyncMock()
	monkeypatch.setattr(message_router_module.ws_manager, "broadcast_to_user", ws_broadcast)
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
			{"type": "file", "file_path": "1/demo.txt", "file_name": "demo.txt", "user_id": 1},
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
		ws_broadcast.assert_awaited()

		token = security.create_access_token(1)
		download = client.get("/api/v1/messages/2/download", headers={"Authorization":f"Bearer {token}"})
		assert download.status_code == 200
		assert download.content == b"demo"

		view = client.get("/api/v1/messages/2/view", headers={"Authorization":f"Bearer {token}"})
		assert view.status_code == 415


def test_download_with_r2_storage_redirect(monkeypatch):
	file_service = AsyncMock()
	message_service = AsyncMock()

	class R2FileRepo:
		async def get_presigned_url(self, file_path: str, as_download: bool, download_name: str | None = None):
			assert file_path == "1/demo.txt"
			assert as_download is True
			assert download_name == "demo.txt"
			return "https://r2.example.com/1/demo.txt?signed=1"

	file_service.get_file_for_user.return_value = type(
		"FileMessage",
		(),
		{"type": "file", "file_path": "1/demo.txt", "file_name": "demo.txt", "user_id": 1},
	)()

	app = FastAPI()
	app.include_router(message_router, prefix="/api/v1")
	app.dependency_overrides[get_current_user_id] = lambda: 1
	app.dependency_overrides[get_message_service] = lambda: message_service
	app.dependency_overrides[get_file_service] = lambda: file_service
	app.dependency_overrides[get_file_repo] = lambda: R2FileRepo()
	client = TestClient(app)

	token = security.create_access_token(1)
	download = client.get(f"/api/v1/messages/2/download?token={token}", follow_redirects = False)

	assert download.status_code == 302
	assert download.headers["location"] == "https://r2.example.com/1/demo.txt?signed=1"


def test_direct_upload_api_flow(monkeypatch):
	message_service = AsyncMock()
	file_service = AsyncMock()
	ws_broadcast = AsyncMock()
	monkeypatch.setattr(message_router_module.ws_manager, "broadcast_to_user", ws_broadcast)
	file_service.create_direct_upload.return_value = {
		"upload_url":"https://r2.example.com/upload",
		"file_name":"demo.txt",
		"file_size":4,
		"file_type":"text/plain",
		"file_path":"1/demo.txt",
		"type":"file",
	}
	file_service.complete_direct_upload.return_value = _msg_payload(3, msg_type="file") | {
		"fileName":"demo.txt",
		"fileSize":4,
		"fileType":"text/plain",
		"filePath":"1/demo.txt",
	}

	app = FastAPI()
	app.include_router(message_router, prefix="/api/v1")
	app.dependency_overrides[get_current_user_id] = lambda: 1
	app.dependency_overrides[get_message_service] = lambda: message_service
	app.dependency_overrides[get_file_service] = lambda: file_service
	client = TestClient(app)

	prepare = client.post(
		"/api/v1/messages/upload-url",
		json={"fileName":"demo.txt", "fileSize":4, "fileType":"text/plain", "device":"desktop"},
	)
	assert prepare.status_code == 200
	assert prepare.json()["uploadUrl"] == "https://r2.example.com/upload"
	assert prepare.json()["filePath"] == "1/demo.txt"

	complete = client.post(
		"/api/v1/messages/upload-complete",
		json={
			"fileName":"demo.txt",
			"fileSize":4,
			"fileType":"text/plain",
			"filePath":"1/demo.txt",
			"device":"desktop",
			"type":"file",
		},
	)
	assert complete.status_code == 200
	assert complete.json()["id"] == 3
	ws_broadcast.assert_awaited()
