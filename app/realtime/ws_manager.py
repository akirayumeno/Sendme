from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
	def __init__(self):
		self._connections: dict[int, set[WebSocket]] = defaultdict(set)

	async def connect(self, user_id: int, websocket: WebSocket):
		await websocket.accept()
		self._connections[user_id].add(websocket)

	def disconnect(self, user_id: int, websocket: WebSocket):
		sockets = self._connections.get(user_id)
		if not sockets:
			return
		sockets.discard(websocket)
		if not sockets:
			self._connections.pop(user_id, None)

	async def broadcast_to_user(self, user_id: int, payload: dict):
		sockets = list(self._connections.get(user_id, set()))
		for ws in sockets:
			try:
				await ws.send_json(payload)
			except Exception:
				self.disconnect(user_id, ws)


ws_manager = ConnectionManager()
