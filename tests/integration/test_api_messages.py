# 集成测试 (Integration Tests)
# test_api_messages.py

from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy.orm import Session

from app.models.models import Message

# 创建测试客户端
client = TestClient(app)


def test_get_messages_empty(client: TestClient):
	"""测试当数据库中没有消息时，GET /messages 返回一个空列表。"""

	response = client.get("/messages")

	assert response.status_code == 200
	assert response.json() == []


def test_get_messages_basic_retrieval(client: TestClient, db_session: Session):
	"""测试可以成功获取插入到数据库中的所有消息。"""

	# 准备数据：手动将三条消息插入到测试数据库中
	msg1 = Message(content="First message")
	msg2 = Message(content="Second message")
	msg3 = Message(content="Third message")

	db_session.add_all([msg1, msg2, msg3])
	db_session.commit()

	# 执行测试：发送 GET 请求
	response = client.get("/messages")

	# 验证结果
	assert response.status_code == 200
	data = response.json()

	# 验证返回了三条消息
	assert len(data) == 3

	# 验证消息按 updated_at 倒序排列（即最新消息在前）
	# 由于我们是按顺序插入的，msg3 应该是最新的，在列表最前面
	assert data[0]['content'] == "Third message"
	assert data[2]['content'] == "First message"
