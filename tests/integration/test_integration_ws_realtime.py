import asyncio

from fastapi.testclient import TestClient

from app.core import security
from app.main import app
from app.realtime.ws_manager import ws_manager


def test_ws_realtime_event_flow():
	token = security.create_access_token(1)

	with TestClient(app) as client:
		with client.websocket_connect(f"/api/v1/ws/messages?token={token}") as websocket:
			asyncio.run(ws_manager.send_personal_message(1, {"event":"message.updated", "message_id":123}))
			assert websocket.receive_json() == {"event":"message.updated", "message_id":123}
