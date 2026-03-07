from io import BytesIO
from pathlib import Path
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
	MessagePermissionError,
	QuotaExceededError,
)
from app.services.file_service import FileService


@pytest.fixture
def file_service(tmp_path):
	file_repo = AsyncMock()
	file_repo.temp_dir = tmp_path
	message_repo = AsyncMock()
	user_repo = AsyncMock()
	service = FileService(file_repo=file_repo, message_repo=message_repo, user_repo=user_repo)
	return service, file_repo, message_repo, user_repo


@pytest.mark.asyncio
class TestFileService:
	async def test_handle_initial_upload_success(self, file_service):
		service, file_repo, _, _ = file_service
		file_repo.save.return_value = 123

		upload = UploadFile(
			filename="a.txt",
			file=BytesIO(b"hello"),
			headers=Headers({"content-type": "text/plain"}),
		)

		result = await service.handle_initial_upload(upload)

		assert result["original_filename"] == "a.txt"
		assert result["size_bytes"] == 123
		assert result["mime_type"] == "text/plain"
		assert "temp_filename" in result

	async def test_handle_initial_upload_aborted(self, file_service):
		service, file_repo, _, _ = file_service
		file_repo.save.side_effect = RuntimeError("stream broken")

		upload = UploadFile(
			filename="a.txt",
			file=BytesIO(b"hello"),
			headers=Headers({"content-type": "text/plain"}),
		)

		with pytest.raises(FileUploadAbortedError):
			await service.handle_initial_upload(upload)

	async def test_finalize_file_message_temp_missing(self, file_service):
		service, _, _, _ = file_service
		schema = FileMessageCreate(
			user_id=1,
			device=DeviceType.desktop,
			type=MessageType.file,
			file_name="a.txt",
			file_size=10,
			file_type="text/plain",
			file_path="1/a.txt",
		)

		with pytest.raises(FilePathNotFoundError):
			await service.finalize_file_message(schema=schema, temp_filename="not_exists.tmp", file_size=10)

	async def test_finalize_file_message_success(self, file_service):
		service, file_repo, message_repo, user_repo = file_service
		temp_filename = "tmp.bin"
		(service.file_repo.temp_dir / temp_filename).write_bytes(b"abc")
		user_repo.get_used_capacity.return_value = 0

		schema = FileMessageCreate(
			user_id=1,
			device=DeviceType.desktop,
			type=MessageType.file,
			file_name="a.txt",
			file_size=3,
			file_type="text/plain",
			file_path="1/a.txt",
		)

		message_repo.create_message.return_value = SimpleNamespace(id=1)

		result = await service.finalize_file_message(schema=schema, temp_filename=temp_filename, file_size=3)

		assert result.id == 1
		file_repo.move_to_final.assert_awaited_once_with(temp_filename, "1/a.txt")
		user_repo.update_used_capacity.assert_awaited_once_with(1, 3)

	async def test_check_quota_exceeded(self, file_service, monkeypatch):
		service, file_repo, _, user_repo = file_service
		user_repo.get_used_capacity.return_value = 100
		monkeypatch.setattr("app.services.file_service.settings.DEFAULT_MAX_CAPACITY_BYTES", 120)

		with pytest.raises(QuotaExceededError):
			await service._check_quota(user_id=1, temp_filename="tmp.bin", file_size=30)

		file_repo.delete_temp.assert_awaited_once_with("tmp.bin")

	async def test_delete_existing_file_success(self, file_service):
		service, file_repo, message_repo, user_repo = file_service
		message_repo.get_by_message_id.return_value = SimpleNamespace(user_id=1, file_path="1/a.txt")
		message_repo.delete_message.return_value = 50
		user_repo.update_used_capacity.return_value = 150

		used = await service.delete_existing_file(message_id=10, user_id=1)

		assert used == 150
		file_repo.delete.assert_awaited_once_with("1/a.txt", is_temp=False)

	async def test_delete_existing_file_permission_denied(self, file_service):
		service, _, message_repo, _ = file_service
		message_repo.get_by_message_id.return_value = SimpleNamespace(user_id=2, file_path="1/a.txt")

		with pytest.raises(MessagePermissionError):
			await service.delete_existing_file(message_id=10, user_id=1)

	async def test_get_file_path_for_user(self, file_service):
		service, _, message_repo, _ = file_service
		message_repo.get_by_message_id.return_value = SimpleNamespace(user_id=1, file_path="1/a.txt")

		path = await service.get_file_path_for_user(message_id=10, user_id=1)
		assert path == "1/a.txt"

	async def test_get_file_path_for_user_no_path(self, file_service):
		service, _, message_repo, _ = file_service
		message_repo.get_by_message_id.return_value = SimpleNamespace(user_id=1, file_path=None)

		with pytest.raises(FilePathNotFoundError):
			await service.get_file_path_for_user(message_id=10, user_id=1)
