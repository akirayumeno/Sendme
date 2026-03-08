from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.dependencies import get_user_id_from_token
from app.realtime.ws_manager import ws_manager

router = APIRouter(prefix = "/ws", tags = ["realtime"])


@router.websocket("/messages")
async def messages_ws(websocket: WebSocket):
	"""WebSocket endpoint for per-user realtime message events.

	Client must pass access token via query string: ?token=<jwt>.
	Once connected, server can push message update/delete events to this socket.
	"""
	token = websocket.query_params.get("token")
	if not token:
		await websocket.close(code = 1008, reason = "Missing token")
		return

	try:
		user_id = get_user_id_from_token(token)
	except ValueError:
		await websocket.close(code = 1008, reason = "Invalid token")
		return

	await ws_manager.connect(user_id, websocket)
	try:
		while True:
			# Keep connection open; client can send ping/noop.
			await websocket.receive_text()
	except WebSocketDisconnect:
		ws_manager.disconnect(user_id, websocket)
