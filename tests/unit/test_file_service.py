from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.core.enums import DeviceType, MessageType
from app.schemas.schemas import FileMessageCreate
from app.services.exceptions import (
	FilePathNotFoundError,
	FileUploadAbortedError,
	MessageNotFoundError,
	MessagePermissionError,
	QuotaExceededError,
)
from app.services.file_service import FileService
from app.storage.exceptions import MessageNotFoundError as RepoMessageNotFoundError


@pytest.fixture
def file_service(tmp_path):
	file_repo = AsyncMock()
	file_repo.temp_dir = tmp_path
	message_repo = AsyncMock()
	user_repo = AsyncMock()
	redis_repo = AsyncMock()
	redis_repo.get_storage_used_bytes.return_value = 0
	r2_repo = AsyncMock()
	service = FileService(
		file_repo = file_repo, message_repo = message_repo, user_repo = user_repo, redis_repo = redis_repo
		, r2_repo = r2_repo
	)
	return service, file_repo, message_repo, user_repo, redis_repo


@pytest.mark.asyncio
class TestFileService:
	async def test_handle_initial_upload_success(self, file_service):
		service, file_repo, _, _, _ = file_service
		file_repo.save.return_value = 123

		upload = UploadFile(
			filename = "a.txt",
			file = BytesIO(b"hello"),
			headers = Headers({"content-type":"text/plain"}),
		)

		result = await service.handle_initial_upload(upload)

		assert result["original_filename"] == "a.txt"
		assert result["size_bytes"] == 123
		assert result["mime_type"] == "text/plain"
		assert "temp_filename" in result

	async def test_handle_initial_upload_aborted(self, file_service):
		service, file_repo, _, _, _ = file_service
		file_repo.save.side_effect = RuntimeError("stream broken")

		upload = UploadFile(
			filename = "a.txt",
			file = BytesIO(b"hello"),
			headers = Headers({"content-type":"text/plain"}),
		)

		with pytest.raises(FileUploadAbortedError):
			await service.handle_initial_upload(upload)

	async def test_handle_initial_upload_file_too_large(self, file_service, monkeypatch):
		service, file_repo, _, _, _ = file_service
		file_repo.save.return_value = 21
		monkeypatch.setattr("app.services.file_service.settings.MAX_FILE_SIZE_BYTES", 20)

		upload = UploadFile(
			filename = "big.txt",
			file = BytesIO(b"hello"),
			headers = Headers({"content-type":"text/plain"}),
		)

		with pytest.raises(QuotaExceededError):
			await service.handle_initial_upload(upload)

		file_repo.delete_temp.assert_awaited_once()

	async def test_finalize_file_message_temp_missing(self, file_service):
		service, _, _, _, _ = file_service
		schema = FileMessageCreate(
			user_id = 1,
			device = DeviceType.desktop,
			type = MessageType.file,
			fileName = "1231231.pdf",
			fileSize = 123,
			fileType = "pdf",
			filePath = "cloudflare.r2.com"
		)

		with pytest.raises(FilePathNotFoundError):
			await service.finalize_file_message(schema = schema, temp_filename = "not_exists.tmp", file_size = 10)

	async def test_finalize_file_message_success(self, file_service):
		service, file_repo, message_repo, user_repo, redis_repo = file_service
		temp_filename = "tmp.bin"
		(service.file_repo.temp_dir / temp_filename).write_bytes(b"abc")
		user_repo.get_used_capacity.return_value = 0

		schema = FileMessageCreate(
			user_id = 1,
			device = DeviceType.desktop,
			type = MessageType.file,
			fileName = "1231231.pdf",
			fileSize = 123,
			fileType = "pdf",
			filePath = "cloudflare.r2.com"
		)

		message_repo.create_message.return_value = SimpleNamespace(id = 1)

		result = await service.finalize_file_message(schema = schema, temp_filename = temp_filename, file_size = 3)

		assert result.id == 1
		file_repo.move_to_final.assert_awaited_once_with(temp_filename, "1/a.txt")
		user_repo.update_used_capacity.assert_awaited_once_with(1, 3)
		redis_repo.set_message_ttl.assert_awaited_once_with(1)
		redis_repo.incr_storage_used_bytes.assert_awaited_once_with(3)

	async def test_create_direct_upload_success(self, file_service):
		service, file_repo, _, user_repo, redis_repo = file_service
		user_repo.get_used_capacity.return_value = 0
		redis_repo.get_storage_used_bytes.return_value = 0
		file_repo.get_presigned_upload_url.return_value = "https://r2.example.com/upload"

		result = await service.create_direct_upload(
			user_id = 1,
			file_name = "photo.png",
			file_size = 10,
			file_type = "image/png",
			device = DeviceType.desktop,
		)

		assert result["upload_url"] == "https://r2.example.com/upload"
		assert result["file_name"] == "photo.png"
		assert result["file_path"].startswith("1/")
		assert result["type"] == MessageType.image
		file_repo.get_presigned_upload_url.assert_awaited_once()

	async def test_complete_direct_upload_success(self, file_service):
		service, file_repo, message_repo, user_repo, redis_repo = file_service
		user_repo.get_used_capacity.return_value = 0
		redis_repo.get_storage_used_bytes.return_value = 0
		file_repo.get_object_metadata.return_value = {"ContentLength":3}
		message_repo.create_message.return_value = SimpleNamespace(id = 2)

		schema = FileMessageCreate(
			user_id = 1,
			device = DeviceType.desktop,
			type = MessageType.file,
			fileName = "1231231.pdf",
			fileSize = 123,
			fileType = "pdf",
			filePath = "cloudflare.r2.com"
		)

		result = await service.complete_direct_upload(schema)

		assert result.id == 2
		message_repo.create_message.assert_awaited_once()
		user_repo.update_used_capacity.assert_awaited_once_with(1, 3)
		redis_repo.set_message_ttl.assert_awaited_once_with(2)

	async def test_complete_direct_upload_size_mismatch(self, file_service):
		service, file_repo, _, user_repo, redis_repo = file_service
		user_repo.get_used_capacity.return_value = 0
		redis_repo.get_storage_used_bytes.return_value = 0
		file_repo.get_object_metadata.return_value = {"ContentLength":2}

		schema = FileMessageCreate(
			user_id = 1,
			device = DeviceType.desktop,
			type = MessageType.file,
			fileName = "1231231.pdf",
			fileSize = 123,
			fileType = "pdf",
			filePath = "cloudflare.r2.com"
		)

		with pytest.raises(FileUploadAbortedError):
			await service.complete_direct_upload(schema)

		file_repo.delete.assert_awaited_once_with("1/a.txt", is_temp = False)

	async def test_check_quota_exceeded(self, file_service, monkeypatch):
		service, file_repo, _, user_repo, _ = file_service
		user_repo.get_used_capacity.return_value = 100
		monkeypatch.setattr("app.services.file_service.settings.DEFAULT_MAX_CAPACITY_BYTES", 120)

		with pytest.raises(QuotaExceededError):
			await service._check_quota(user_id = 1, temp_filename = "tmp.bin", file_size = 30)

		file_repo.delete_temp.assert_awaited_once_with("tmp.bin")

	async def test_check_global_storage_exceeded(self, file_service, monkeypatch):
		service, file_repo, _, user_repo, redis_repo = file_service
		user_repo.get_used_capacity.return_value = 0
		redis_repo.get_storage_used_bytes.return_value = 90
		monkeypatch.setattr("app.services.file_service.settings.DEFAULT_MAX_CAPACITY_BYTES", 1_000)
		monkeypatch.setattr("app.services.file_service.settings.GLOBAL_MAX_STORAGE_BYTES", 100)

		with pytest.raises(QuotaExceededError):
			await service._check_quota(user_id = 1, temp_filename = "tmp.bin", file_size = 20)

		file_repo.delete_temp.assert_awaited_once_with("tmp.bin")

	async def test_delete_existing_file_success(self, file_service):
		service, file_repo, message_repo, user_repo, redis_repo = file_service
		message_repo.get_by_message_id.return_value = SimpleNamespace(user_id = 1, file_path = "1/a.txt")
		message_repo.delete_message.return_value = 50
		user_repo.update_used_capacity.return_value = 150

		used = await service.delete_existing_file(message_id = 10, user_id = 1)

		assert used == 150
		user_repo.update_used_capacity.assert_awaited_once_with(1, -50)
		file_repo.delete.assert_awaited_once_with("1/a.txt", is_temp = False)
		redis_repo.delete_timer.assert_awaited_once_with(10)
		redis_repo.decr_storage_used_bytes.assert_awaited_once_with(50)

	async def test_delete_existing_file_permission_denied(self, file_service):
		service, _, message_repo, _, _ = file_service
		message_repo.get_by_message_id.return_value = SimpleNamespace(user_id = 2, file_path = "1/a.txt")

		with pytest.raises(MessagePermissionError):
			await service.delete_existing_file(message_id = 10, user_id = 1)

	async def test_get_file_path_for_user(self, file_service):
		service, _, message_repo, _, _ = file_service
		message_repo.get_by_message_id.return_value = SimpleNamespace(user_id = 1, file_path = "1/a.txt")

		path = await service.get_file_path_for_user(message_id = 10, user_id = 1)
		assert path == "1/a.txt"

	async def test_get_file_path_for_user_no_path(self, file_service):
		service, _, message_repo, _, _ = file_service
		message_repo.get_by_message_id.return_value = SimpleNamespace(user_id = 1, file_path = None)

		with pytest.raises(FilePathNotFoundError):
			await service.get_file_path_for_user(message_id = 10, user_id = 1)

	async def test_get_file_for_user_success(self, file_service):
		service, _, message_repo, _, _ = file_service
		message = SimpleNamespace(id = 10, user_id = 1, file_path = "1/a.txt")
		message_repo.get_by_message_id.return_value = message

		result = await service.get_file_for_user(message_id = 10, user_id = 1)

		assert result.id == 10

	async def test_get_file_for_user_permission_denied(self, file_service):
		service, _, message_repo, _, _ = file_service
		message_repo.get_by_message_id.return_value = SimpleNamespace(id = 10, user_id = 2, file_path = "2/a.txt")

		with pytest.raises(MessagePermissionError):
			await service.get_file_for_user(message_id = 10, user_id = 1)

	async def test_get_file_for_user_not_found(self, file_service):
		service, _, message_repo, _, _ = file_service
		message_repo.get_by_message_id.side_effect = RepoMessageNotFoundError(message_id = 10)

		with pytest.raises(MessageNotFoundError):
			await service.get_file_for_user(message_id = 10, user_id = 1)
