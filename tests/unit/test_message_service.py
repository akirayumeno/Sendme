from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.enums import MessageType, MessageStatus
from app.schemas.schemas import TextMessageCreate
from app.services.exceptions import MessagePermissionError
from app.services.message_service import MessageService


@pytest.mark.asyncio
class TestMessageService:
	@pytest.fixture
	def mock_repos(self):
		"""Create mocks for all repository dependencies."""
		message_repo = AsyncMock()
		user_repo = AsyncMock()
		file_service = AsyncMock()
		redis_repo = AsyncMock()
		service = MessageService(message_repo, user_repo, file_service, redis_repo)
		return service, message_repo, user_repo, file_service, redis_repo

	async def test_create_text_message_success(self, mock_repos):
		service, message_repo, _, _, redis_repo = mock_repos

		# Setup Mocks
		schema = TextMessageCreate(
			user_id = 1,
			content = "Hello World",
			type = MessageType.text
		)

		await service.create_text_message(schema)
		message_repo.create_message.assert_called_once()
		args = message_repo.create_message.call_args[0][0]
		assert args["status"] == MessageStatus.sent
		assert args["file_size"] == 0
		assert args["content"] == "Hello World"
		redis_repo.set_message_ttl.assert_awaited_once()

	async def test_get_history_pagination(self, mock_repos):
		service, message_repo, _, _, _ = mock_repos

		# test page
		await service.get_history(user_id = 1, page = 2, page_size = 10)

		# assert：offset (2-1)*10 = 10
		message_repo.get_by_user.assert_called_once_with(1, 10, 10)

	async def test_delete_text_message_success(self, mock_repos):
		service, message_repo, _, _, redis_repo = mock_repos

		mock_msg = MagicMock()
		mock_msg.user_id = 1
		mock_msg.type = MessageType.text
		message_repo.get_by_message_id.return_value = mock_msg

		result = await service.delete_message(message_id = 100, user_id = 1)

		assert result is True
		message_repo.delete_message.assert_called_once_with(100)
		redis_repo.delete_timer.assert_awaited_once_with(100)

	async def test_delete_file_message_success(self, mock_repos):
		service, message_repo, _, file_service, _ = mock_repos

		mock_msg = MagicMock()
		mock_msg.user_id = 1
		mock_msg.type = MessageType.file
		message_repo.get_by_message_id.return_value = mock_msg

		await service.delete_message(message_id = 200, user_id = 1)

		file_service.delete_existing_file.assert_called_once_with(200, 1)

	async def test_delete_message_permission_denied(self, mock_repos):
		service, message_repo, _, _, _ = mock_repos

		# 1. mock the message from user A (id=999)
		mock_msg = MagicMock()
		mock_msg.user_id = 999
		message_repo.get_by_message_id.return_value = mock_msg

		# 2. user B (id=1) try to delete, should raise an error
		with pytest.raises(MessagePermissionError):
			await service.delete_message(message_id = 100, user_id = 1)
