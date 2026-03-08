import asyncio
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
	def __init__(self):
		# Store active connections: {user_id: {websocket1, websocket2}}
		# Using a set allows a single user to stay connected on multiple devices (phone/PC)
		self._connections: Dict[int, Set[WebSocket]] = defaultdict(set)

	async def connect(self, user_id: int, websocket: WebSocket):
		"""Accepts a new connection and tracks it by user_id."""
		await websocket.accept()
		self._connections[user_id].add(websocket)

	def disconnect(self, user_id: int, websocket: WebSocket):
		"""Removes a disconnected socket and cleans up the user entry if empty."""
		if user_id in self._connections:
			self._connections[user_id].discard(websocket)
			# Remove the key if no more active sockets for this user to save memory
			if not self._connections[user_id]:
				self._connections.pop(user_id)

	async def send_personal_message(self, user_id: int, payload: dict):
		"""Sends a JSON message to all active sessions of a specific user."""
		sockets = self._connections.get(user_id, set())
		if not sockets:
			return

		# Use asyncio.gather to send messages to all user's devices concurrently
		tasks = [self._safe_send(user_id, ws, payload) for ws in list(sockets)]
		await asyncio.gather(*tasks)

	async def _safe_send(self, user_id: int, websocket: WebSocket, payload: dict):
		"""Internal helper to handle individual send errors."""
		try:
			await websocket.send_json(payload)
		except Exception:
			# If sending fails (e.g., client closed abruptly), clean up immediately
			self.disconnect(user_id, websocket)

	async def broadcast_all(self, payload: dict):
		"""Broadcasts a message to EVERY connected user in the system."""
		for user_id in list(self._connections.keys()):
			await self.send_personal_message(user_id, payload)


ws_manager = ConnectionManager()
