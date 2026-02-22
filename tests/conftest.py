import asyncio

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.database import Base
from app.storage.sqlalchemy_repo import UserRepository, MessageRepository


# --- Engine Configuration ---

@pytest.fixture(scope = "session")
def engine():
	"""
	Create an asynchronous engine for SQLite.
	The 'sqlite+aiosqlite' prefix is required for async support.
	Using ':memory:' ensures a fresh database for each test session.
	"""
	return create_async_engine("sqlite+aiosqlite:///:memory:", echo = False)


# --- Schema Management ---

@pytest.fixture(scope = "session", autouse = True)
async def tables(engine):
	"""
	Initialize database tables.
	Since Base.metadata.create_all is a synchronous method,
	it must be run using 'run_sync' within an async connection.
	"""
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
	yield
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.drop_all)


# --- Session & Transaction Management ---

@pytest.fixture
async def db_session(engine):
	"""
	Provide a functional-scoped AsyncSession.
	We manually manage the connection and transaction to ensure
	each test is isolated and can be rolled back effectively.
	"""
	connection = await engine.connect()
	# Begin a savepoint/transaction
	transaction = await connection.begin()

	# expire_on_commit=False prevents SQLAlchemy from wiping
	# object attributes after a commit, which is vital for async tests.
	session = AsyncSession(
		bind = connection,
		expire_on_commit = False
	)

	yield session

	# Cleanup: Close session first, rollback the transaction to
	# wipe test data, and finally release the connection.
	await session.close()
	await transaction.rollback()
	await connection.close()


# --- Repository Fixtures ---

@pytest.fixture
async def user_db(db_session: AsyncSession) -> UserRepository:
	"""Inject the async session into the UserRepository."""
	return UserRepository(db_session)


@pytest.fixture
async def message_db(db_session: AsyncSession) -> MessageRepository:
	"""Inject the async session into the MessageRepository."""
	return MessageRepository(db_session)


# --- Event Loop Management ---

@pytest.fixture(scope = "session")
def event_loop():
	"""
	Explicitly manage the event loop for the session scope.
	This prevents 'ScopeMismatch' errors when async fixtures
	need to persist across multiple tests.
	"""
	try:
		loop = asyncio.get_running_loop()
	except RuntimeError:
		loop = asyncio.new_event_loop()
	yield loop
	loop.close()
