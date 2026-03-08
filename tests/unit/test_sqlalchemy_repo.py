from datetime import datetime, timedelta, timezone

import pytest

from app.core.enums import MessageStatus, MessageType
from app.storage.exceptions import MessageNotFoundError, TokenNotFoundErrorByJti, UserConstraintError, UserNotFoundErrorById
from app.storage.sqlalchemy_repo import MessageRepository, RefreshTokenRepository, UserRepository


def _email(name: str) -> str:
	return f"{name}@example.com"


async def test_create_user_success(user_db: UserRepository):
	user = await user_db.create_user("testuser", "hashedpassword", _email("testuser"))
	assert user.id is not None
	assert user.username == "testuser"
	assert user.email == _email("testuser")
	assert user.is_verified is False


async def test_get_user_by_username_success(user_db: UserRepository):
	await user_db.create_user("find_me", "password", _email("find_me"))
	found = await user_db.get_user_by_username("find_me")
	assert found is not None


async def test_get_non_existent_user_by_id(user_db: UserRepository):
	with pytest.raises(UserNotFoundErrorById):
		await user_db.get_user_by_id(123)


async def test_create_user_duplicate_username(user_db: UserRepository):
	await user_db.create_user("duplicate_me", "password123", _email("duplicate_me"))
	with pytest.raises(UserConstraintError):
		await user_db.create_user("duplicate_me", "other_password", _email("other_user"))


async def test_update_user_quota_success(user_db: UserRepository):
	user = await user_db.create_user("quota_user", "password", _email("quota_user"))
	updated = await user_db.update_user(user.id, {"used_quota_bytes": 5000})
	assert updated.used_quota_bytes == 5000


async def test_update_user_username_duplicate(user_db: UserRepository):
	await user_db.create_user("quota_user1", "password", _email("quota_user1"))
	user2 = await user_db.create_user("quota_user2", "password", _email("quota_user2"))
	with pytest.raises(UserConstraintError):
		await user_db.update_user(user2.id, {"username": "quota_user1"})


async def test_get_capacity_and_used_quota(user_db: UserRepository):
	user = await user_db.create_user("quota_test_user", "password123", _email("quota_test_user"))
	assert await user_db.get_capacity_by_user_id(user.id) == 100 * 1024 * 1024
	assert await user_db.get_used_capacity(user.id) == 0


async def test_get_used_capacity_non_existent_user(user_db):
	assert await user_db.get_used_capacity(9999) == 0


async def test_update_used_capacity_success(user_db):
	user = await user_db.create_user("update_test_user", "password123", _email("update_test_user"))
	assert await user_db.update_used_capacity(user.id, 500) == 500
	assert await user_db.update_used_capacity(user.id, 300) == 800


async def test_update_used_capacity_negative_change(user_db):
	user = await user_db.create_user("decrease_user", "password123", _email("decrease_user"))
	await user_db.update_used_capacity(user.id, 1000)
	assert await user_db.update_used_capacity(user.id, -400) == 600


async def test_get_user_with_capacity_lock_success(user_db):
	user = await user_db.create_user("lock_user", "password123", _email("lock_user"))
	locked_user = await user_db.get_user_with_capacity_lock(user.id)
	assert locked_user.id == user.id


async def test_get_user_with_capacity_lock_not_found(user_db):
	with pytest.raises(UserNotFoundErrorById):
		await user_db.get_user_with_capacity_lock(9999)


async def test_create_message_success(db_session):
	repo = MessageRepository(db_session)
	msg = await repo.create_message(
		{
			"user_id": 1,
			"type": MessageType.text,
			"content": "Hello World",
			"status": MessageStatus.sent,
			"file_size": 0,
		}
	)
	assert msg.id is not None
	assert msg.content == "Hello World"


async def test_get_message_not_found(db_session):
	repo = MessageRepository(db_session)
	with pytest.raises(MessageNotFoundError):
		await repo.get_by_message_id(999)


async def test_hard_delete_logic(db_session):
	repo = MessageRepository(db_session)
	msg = await repo.create_message(
		{
			"user_id": 1,
			"type": MessageType.file,
			"file_size": 5 * 1024 * 1024,
			"is_deleted": False,
		}
	)
	await repo.delete_message(msg.id)
	with pytest.raises(MessageNotFoundError):
		await repo.get_by_message_id(msg.id)


async def test_create_and_get_unused_token(db_session):
	repo = RefreshTokenRepository(db_session)
	jti = "test-jti-123"
	expires = datetime.now(timezone.utc) + timedelta(days = 1)
	await repo.create_token_record(user_id = 1, token_jti = jti, expires_at = expires)
	token = await repo.get_unused_token(jti)
	assert token.jti == jti


async def test_get_expired_token_fails(db_session):
	repo = RefreshTokenRepository(db_session)
	jti = "expired-jti"
	expires = datetime.now(timezone.utc) - timedelta(hours = 1)
	await repo.create_token_record(user_id = 1, token_jti = jti, expires_at = expires)
	with pytest.raises(TokenNotFoundErrorByJti):
		await repo.get_unused_token(jti)


async def test_delete_all_user_tokens(db_session):
	repo = RefreshTokenRepository(db_session)
	user_id = 100
	await repo.create_token_record(user_id, "jti1", datetime.now(timezone.utc) + timedelta(days = 1))
	await repo.create_token_record(user_id, "jti2", datetime.now(timezone.utc) + timedelta(days = 1))
	await repo.delete_all_user_tokens(user_id)
	with pytest.raises(TokenNotFoundErrorByJti):
		await repo.get_unused_token("jti1")
