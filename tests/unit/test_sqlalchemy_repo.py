from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.core.enums import MessageType, MessageStatus
from app.storage.exceptions import UserNotFoundErrorById, UserConstraintError, RepositoryError, \
	MessageNotFoundError
from app.storage.sqlalchemy_repo import UserRepository, MessageRepository, RefreshTokenRepository


# --------------------------
# UserRepository Tests
# --------------------------
async def test_create_user_success(user_db: UserRepository):
	username = "testuser"
	password = "hashedpassword"

	user = await user_db.create_user(username, password)

	assert user.id is not None
	assert user.username == username
	assert user.hashed_password == password
	assert user.is_verified is False
	assert user.max_quota_bytes == 100 * 1024 * 1024

	fetched_user = await user_db.get_user_by_id(user.id)
	assert fetched_user.username == username


async def test_get_user_by_username_success(user_db: UserRepository):
	username = "find_me"
	await user_db.create_user(username, "password")

	found_user = await user_db.get_user_by_username(username)

	assert found_user is not None
	assert found_user.username == username


async def test_get_non_existent_user_by_id(user_db: UserRepository):
	user_id = 123
	with pytest.raises(UserNotFoundErrorById) as excinfo:
		await user_db.get_user_by_id(user_id)
	assert str(user_id) in str(excinfo.value)


async def test_create_user_duplicate_username(user_db: UserRepository):
	username = "duplicate_me"
	password = "password123"

	await user_db.create_user(username, password)

	with pytest.raises(UserConstraintError) as excinfo:
		await user_db.create_user(username, "other_password")

	assert f"User {username} already exists in the database" in str(excinfo.value)


async def test_create_user_unexpected_repository_error(user_db):
	user_db.db.add = MagicMock(side_effect = Exception("Database connection lost"))

	with pytest.raises(RepositoryError) as excinfo:
		await user_db.create_user("any_user", "password")

	assert "An unknown error occurred while creating a user" in str(excinfo.value)


async def test_get_user_by_id_not_found(user_db: UserRepository):
	non_existent_id = 9999
	with pytest.raises(UserNotFoundErrorById) as excinfo:
		await user_db.get_user_by_id(non_existent_id)

	assert str(non_existent_id) in str(excinfo.value)


async def test_update_user_quota_success(user_db: UserRepository):
	username = "quota_user"
	user = await user_db.create_user(username, "password")
	new_used_quota = 5000
	updates = {"used_quota_bytes":new_used_quota}

	# update used capacity
	updated_user = await user_db.update_user(user.id, updates)

	assert updated_user.used_quota_bytes == new_used_quota


async def test_update_user_username_duplicate(user_db: UserRepository):
	# user1
	username1 = "quota_user1"
	user1 = await user_db.create_user(username1, "password")

	# user2
	username2 = "quota_user2"
	user2 = await user_db.create_user(username2, "password")

	target_user_id = user2.id
	updates = {"username":username1}

	# update used capacity
	with pytest.raises(UserConstraintError) as excinfo:
		await user_db.update_user(target_user_id, updates)

	assert str(target_user_id) in str(excinfo.value)


# ---------------------------------------------------------
# capacity (Getters)
# ---------------------------------------------------------
async def test_get_capacity_and_used_quota(user_db):
	# 1. prepare data
	user = await user_db.create_user("quota_test_user", "password123")

	# 2. test default capacity (100MB)
	max_cap = await user_db.get_capacity_by_user_id(user.id)
	assert max_cap == 100 * 1024 * 1024

	# 3. test get used capacity
	used_cap = await user_db.get_used_capacity(user.id)
	assert used_cap == 0


async def test_get_used_capacity_non_existent_user(user_db):
	# For tests where the user does not exist, return 0 without reporting an error.
	assert await user_db.get_used_capacity(9999) == 0


# ---------------------------------------------------------
# Capacity update test (Update Logic)
# ---------------------------------------------------------

async def test_update_used_capacity_success(user_db):
	user = await user_db.create_user("update_test_user", "password123")

	# Add 500 bytes
	new_total = await user_db.update_used_capacity(user.id, 500)
	assert new_total == 500

	# Add another 300 bytes (cumulative test)
	final_total = await user_db.update_used_capacity(user.id, 300)
	assert final_total == 800

	# Verify the persistent state in the database
	assert await user_db.get_used_capacity(user.id) == 800


async def test_update_used_capacity_negative_change(user_db):
	# Test the reduction in storage space after deleting files.
	user = await user_db.create_user("decrease_user", "password123")
	await user_db.update_used_capacity(user.id, 1000)

	# Reduced by 400 bytes
	remaining = await user_db.update_used_capacity(user.id, -400)
	assert remaining == 600


# ---------------------------------------------------------
# Pessimistic Lock Logic Test
# ---------------------------------------------------------

async def test_get_user_with_capacity_lock_success(user_db):
	user = await user_db.create_user("lock_user", "password123")

	# Verify whether the locked user object can be successfully acquired.
	locked_user = await user_db.get_user_with_capacity_lock(user.id)
	assert locked_user.id == user.id
	assert locked_user.username == "lock_user"


async def test_get_user_with_capacity_lock_not_found(user_db):
	# Verify that a correct custom exception is thrown when the user does not exist.
	with pytest.raises(UserNotFoundErrorById) as excinfo:
		await user_db.get_user_with_capacity_lock(9999)

	# Check if the error message contains an incorrect ID.
	assert "9999" in str(excinfo.value)


# ---------------------------------------------------------
# Message Logic Test
# ---------------------------------------------------------
async def test_create_message_success(db_session):
	repo = MessageRepository(db_session)
	data = {
		"user_id":1,
		"type":MessageType.text,
		"content":"Hello World",
		"status":MessageStatus.sent,
		"file_size_bytes":0
	}

	msg = await repo.create_message(data)
	assert msg.id is not None
	assert msg.content == "Hello World"
	assert msg.is_deleted is False


async def test_get_message_not_found(db_session):
	repo = MessageRepository(db_session)
	with pytest.raises(MessageNotFoundError):
		await repo.get_message_by_message_id(999)


async def test_hard_delete_logic(db_session):
	repo = MessageRepository(db_session)
	# create a 5MB message
	file_size = 5 * 1024 * 1024
	msg = await repo.create_message(
		{
			"user_id":1,
			"type":MessageType.file,
			"file_size_bytes":file_size,
			"is_deleted":False
		}
	)

	size = await repo.delete_message(msg.id)
	assert size == file_size

	# 3. A subsequent query should throw a Not Found exception.
	with pytest.raises(MessageNotFoundError):
		await repo.get_message_by_message_id(msg.id)


# ---------------------------------------------------------
# Token repo Test
# ---------------------------------------------------------
async def test_create_and_get_unused_token(db_session):
	repo = RefreshTokenRepository(db_session)
	jti = "test-jti-123"
	expires = datetime.now() + timedelta(days = 1)

	await repo.create_token_record(user_id = 1, token_jti = jti, expires_at = expires)

	token = await repo.get_unused_token(jti)
	assert token.jti == jti


async def test_get_expired_token_fails(db_session):
	repo = RefreshTokenRepository(db_session)
	jti = "expired-jti"
	# Set to expire 1 hour ago
	expires = datetime.now(timezone.utc) - timedelta(hours = 1)
	await repo.create_token_record(user_id = 1, token_jti = jti, expires_at = expires)

	# The repository is likely not found because `expires_at < now()` (throwing a `RepositoryError`).
	with pytest.raises(RepositoryError, match = "not found or already used"):
		await repo.get_unused_token(jti)


async def test_delete_all_user_tokens(db_session):
	repo = RefreshTokenRepository(db_session)
	user_id = 100
	await repo.create_token_record(user_id, "jti1", datetime.now() + timedelta(days = 1))
	await repo.create_token_record(user_id, "jti2", datetime.now() + timedelta(days = 1))

	count = await repo.delete_all_user_tokens(user_id)
	assert count == 2
