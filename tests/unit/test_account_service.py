from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.enums import MessageType
from app.services.account_service import AccountService


@pytest.fixture
def account_service():
	user_repo = AsyncMock()
	message_repo = AsyncMock()
	token_repo = AsyncMock()
	file_service = AsyncMock()
	redis_repo = AsyncMock()
	service = AccountService(
		user_repo = user_repo,
		message_repo = message_repo,
		token_repo = token_repo,
		file_service = file_service,
		redis_repo = redis_repo,
	)
	return service, user_repo, message_repo, token_repo, file_service, redis_repo


@pytest.mark.asyncio
async def test_delete_account_removes_all_user_data(account_service):
	service, user_repo, message_repo, token_repo, file_service, redis_repo = account_service
	user_repo.get_user_by_id.return_value = SimpleNamespace(id = 1, email = "u@example.com")
	message_repo.get_all_by_user.return_value = [
		SimpleNamespace(id = 10, type = MessageType.text, file_path = None),
		SimpleNamespace(id = 11, type = MessageType.image, file_path = "1/image.png"),
		SimpleNamespace(id = 12, type = MessageType.file, file_path = "1/document.docx"),
	]

	result = await service.delete_account(user_id = 1)

	assert result == {"status":"success", "deleted_messages":3}
	message_repo.delete_message.assert_awaited_once_with(10)
	redis_repo.delete_timer.assert_awaited_once_with(10)
	assert file_service.delete_existing_file.await_args_list[0].args == (11, 1)
	assert file_service.delete_existing_file.await_args_list[1].args == (12, 1)
	token_repo.delete_all_user_tokens.assert_awaited_once_with(1)
	redis_repo.clear_otp_state.assert_awaited_once_with("u@example.com")
	redis_repo.clear_otp_attempts.assert_awaited_once_with("u@example.com")
	user_repo.delete_user.assert_awaited_once_with(1)
