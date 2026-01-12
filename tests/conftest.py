# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.database import Base
from app.storage.sqlalchemy_repo import UserRepository, MessageRepository


@pytest.fixture(scope = "session")
def engine():
	return create_engine("sqlite:///:memory:")


@pytest.fixture(scope = "session")
def tables(engine):
	Base.metadata.create_all(engine)
	yield
	Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
	"""provide individual unit test Session，and roll back after test"""
	connection = engine.connect()
	transaction = connection.begin()

	SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = connection)
	session: Session = SessionLocal()

	yield session

	session.close()
	transaction.rollback()
	connection.close()


@pytest.fixture
def user_db(db_session: Session) -> UserRepository:
	return UserRepository(db_session)


@pytest.fixture
def message_db(db_session: Session) -> MessageRepository:
	return MessageRepository(db_session)
