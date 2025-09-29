# Pytest 配置文件，用于 setup/teardown
# tests/conftest.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db  # 导入你的 Base 模型和依赖项函数

# --------------------------
# 1. 配置测试数据库
# --------------------------
# 注意：这个数据库URL应该指向一个专门用于测试的数据库！
TEST_DATABASE_URL = "postgresql://postgres:password@db:5432/sendme_db"
print(f"\n--- DEBUG: Connecting URL is: {TEST_DATABASE_URL} ---\n")

# 创建一个测试引擎和会话
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --------------------------
# 2. 定义数据库会话夹具 (Fixture)
# --------------------------

@pytest.fixture(scope="session")  # session 范围，表示测试会话开始时创建一次
def db_engine():
	"""创建一个测试数据库引擎，并确保所有表都被创建和清理。"""
	# 每次测试运行前，先创建所有表
	Base.metadata.create_all(bind=engine)
	yield engine
	# 每次测试运行后，删除所有表，保持数据库干净
	Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")  # function 范围，表示每个测试函数都会调用一次
def db_session(db_engine):
	"""为每个测试函数提供一个独立的数据库会话。"""
	connection = db_engine.connect()
	transaction = connection.begin()
	session = TestingSessionLocal(bind=connection)

	yield session  # 将会话传递给测试函数

	# 清理：测试结束后，回滚事务，确保测试对数据库的更改不会保留
	session.close()
	transaction.rollback()
	connection.close()


# --------------------------
# 3. 覆盖 FastAPI 的数据库依赖项
# --------------------------

def override_get_db():
	"""覆盖原始的 get_db 依赖项，转而使用我们的测试会话。"""
	try:
		session = TestingSessionLocal()
		yield session
	finally:
		session.close()


# --------------------------
# 4. 定义 FastAPI 测试客户端夹具
# --------------------------

@pytest.fixture(scope="function")  # function 范围，表示每个测试函数都会调用一次
def client(db_session):
	"""返回一个可用于发送请求的 FastAPI 测试客户端。"""
	# 将 FastAPI 应用的依赖项指向我们定义的测试会话
	app.dependency_overrides[get_db] = lambda: db_session

	# 创建并返回测试客户端
	with TestClient(app) as c:
		yield c

	# 清理：测试结束后，移除依赖覆盖
	app.dependency_overrides.clear()