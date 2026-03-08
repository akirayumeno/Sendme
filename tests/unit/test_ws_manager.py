from unittest.mock import AsyncMock

import pytest

from app.realtime.ws_manager import ConnectionManager


@pytest.mark.asyncio
async def test_connect_and_disconnect():
	manager = ConnectionManager()
	ws = AsyncMock()

	await manager.connect(1, ws)
	ws.accept.assert_awaited_once()
	assert ws in manager._connections[1]

	manager.disconnect(1, ws)
	assert 1 not in manager._connections


@pytest.mark.asyncio
async def test_send_personal_message_success():
	manager = ConnectionManager()
	ws1 = AsyncMock()
	ws2 = AsyncMock()
	manager._connections[1] = {ws1, ws2}

	payload = {"event":"message.updated", "message_id":1}
	await manager.send_personal_message(1, payload)

	ws1.send_json.assert_awaited_once_with(payload)
	ws2.send_json.assert_awaited_once_with(payload)


@pytest.mark.asyncio
async def test_broadcast_alias():
	manager = ConnectionManager()
	ws = AsyncMock()
	manager._connections[9] = {ws}

	payload = {"event":"message.deleted", "message_id":99}
	await manager.broadcast_to_user(9, payload)
	ws.send_json.assert_awaited_once_with(payload)
