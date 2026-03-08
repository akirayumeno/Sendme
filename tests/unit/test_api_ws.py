import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.ws import router as ws_router
from app.realtime.ws_manager import ws_manager


def test_ws_rejects_missing_token():
	app = FastAPI()
	app.include_router(ws_router, prefix = "/api/v1")
	client = TestClient(app)

	with pytest.raises(WebSocketDisconnect):
		with client.websocket_connect("/api/v1/ws/messages"):
			pass


def test_ws_rejects_invalid_token(monkeypatch):
	app = FastAPI()
	app.include_router(ws_router, prefix = "/api/v1")
	client = TestClient(app)

	def _raise(_token: str):
		raise ValueError("bad token")

	monkeypatch.setattr("app.api.ws.get_user_id_from_token", _raise)

	with pytest.raises(WebSocketDisconnect):
		with client.websocket_connect("/api/v1/ws/messages?token=bad"):
			pass


def test_ws_receive_user_event(monkeypatch):
	app = FastAPI()
	app.include_router(ws_router, prefix = "/api/v1")
	client = TestClient(app)

	monkeypatch.setattr("app.api.ws.get_user_id_from_token", lambda _token: 1)

	with client.websocket_connect("/api/v1/ws/messages?token=ok") as websocket:
		asyncio.run(ws_manager.send_personal_message(1, {"event":"message.updated", "message_id":7}))
		assert websocket.receive_json() == {"event":"message.updated", "message_id":7}
