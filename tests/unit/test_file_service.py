from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

from app.domain.exceptions import FileQuotaExceededError
from app.domain.models import File
from app.services.file_service import FileService


# ----------------------------------------------------------------------
# 1. Setup/Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def mock_storage_repo():
	mock = AsyncMock()
	mock.save.return_value = 1024
	return mock


@pytest.fixture
def mock_metadata_repo():
	mock = AsyncMock()
	mock.create.return_value = File(
		id = 1,
		user_id = 100,
		file_path = "test_uuid.png",
		file_size_bytes = 1024,
		status = "UPLOADED",
		is_deleted = False
	)
	return mock


@pytest.fixture
def file_service(mock_storage_repo, mock_metadata_repo):
	return FileService(mock_storage_repo, mock_metadata_repo)


# ----------------------------------------------------------------------
# 2. Test Cases
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_upload_success_calls_repos_correctly(file_service, mock_storage_repo, mock_metadata_repo):
	mock_upload_file = MagicMock(spec = UploadFile)
	mock_upload_file.filename = "test_image.png"
	mock_upload_file.read.return_value = b"mock file content"

	user_id = 100
	result = await file_service.upload_file(mock_upload_file, user_id)

	mock_storage_repo.save.assert_called_once()
	mock_metadata_repo.save.assert_called_once()

	assert "file_id" in result
	assert result["file_id"] == user_id


@pytest.mark.asyncio
async def test_upload_failure_on_quota_exceeded(file_service, mock_storage_repo, mock_metadata_repo):
	mock_metadata_repo.check_quota.side_effct = FileQuotaExceededError(
		user_id = 100, current_size = 900, max_size = 1000
	)
	mock_upload_file = MagicMock(spec = UploadFile)
	mock_upload_file.filename = "large_file.png"
	mock_upload_file.read.return_value = b"large content"

	with pytest.raises(FileQuotaExceededError):
		await file_service.upload_file(mock_upload_file, 100)

	mock_storage_repo.save.assert_not_called()
