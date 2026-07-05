import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from starlette import status

from app.core.dependencies import get_current_user_id, get_file_repo, get_file_service, get_message_service, get_user_id_from_token
from app.core.enums import DeviceType, MessageType
from app.realtime.ws_manager import ws_manager
from app.schemas.schemas import FileMessageCreate, MessageResponse, TextMessageCreate, TextMessageRequest
from app.services.exceptions import (
	FilePathNotFoundError,
	FileUploadAbortedError,
	MessagePermissionError,
	QuotaExceededError,
)
from app.services.file_service import FileService
from app.services.message_service import MessageService
from app.storage.file_repo import FileRepo

router = APIRouter(prefix = "/messages", tags = ["messages"])


def _extract_message_id(message) -> int | str | None:
	"""Supports both ORM objects and dict payloads used by tests/fakes."""
	if isinstance(message, dict):
		return message.get("id")
	return getattr(message, "id", None)


def _resolve_file_path(file_repo: FileRepo, relative_path: str) -> Path:
	"""Resolve and validate a file path under upload root to prevent traversal."""
	full_path = (file_repo.upload_dir / relative_path).resolve()
	upload_root = file_repo.upload_dir.resolve()
	if upload_root not in full_path.parents:
		raise HTTPException(status_code = 400, detail = "Invalid file path.")
	return full_path


def _resolve_request_user_id(token: str | None, authorization: str | None) -> int:
	"""Resolve user id from either query token or Authorization header."""
	auth_token = token
	if not auth_token and authorization and authorization.lower().startswith("bearer "):
		auth_token = authorization.split(" ", 1)[1]
	if not auth_token:
		raise HTTPException(status_code = 401, detail = "Not authenticated")
	try:
		return get_user_id_from_token(auth_token)
	except ValueError as exc:
		raise HTTPException(status_code = 401, detail = "Invalid access token") from exc


async def _file_response(file_repo: FileRepo, relative_path: str, as_download: bool, download_name: str | None = None):
	"""Build a file response with optional download filename behavior."""
	if hasattr(file_repo, "get_presigned_url"):
		url = await file_repo.get_presigned_url(relative_path, as_download = as_download, download_name = download_name)
		return RedirectResponse(url = url, status_code = 302)

	full_path = _resolve_file_path(file_repo, relative_path)
	if not full_path.exists():
		raise HTTPException(status_code = 404, detail = "File not found.")
	filename = (download_name or os.path.basename(relative_path)) if as_download else None
	return FileResponse(path = str(full_path), filename = filename)


@router.post("/text", response_model = MessageResponse)
async def send_text(
		payload: TextMessageRequest,
		user_id: int = Depends(get_current_user_id),
		service: MessageService = Depends(get_message_service),
):
	"""Create text message and emit realtime update event."""
	schema = TextMessageCreate(
		user_id = user_id,
		content = payload.content,
		type = MessageType.text,
		device = payload.device,
	)
	message = await service.create_text_message(schema)
	message_id = _extract_message_id(message)
	await ws_manager.broadcast_to_user(
		user_id,
		{"event":"message.updated", "message_id":message_id},
	)
	return message


@router.get("/history", response_model = list[MessageResponse])
async def get_history(
		page: int = Query(1, ge = 1),
		user_id: int = Depends(get_current_user_id),
		service: MessageService = Depends(get_message_service),
):
	"""Return paginated message history for current user."""
	return await service.get_history(user_id = user_id, page = page)


@router.post("/upload", response_model = MessageResponse)
async def upload_file(
		file: UploadFile = File(...),
		device: DeviceType = Form(DeviceType.desktop),
		user_id: int = Depends(get_current_user_id),
		service: FileService = Depends(get_file_service),
):
	"""Handle file upload, persist metadata, and emit realtime update."""
	if not file.filename:
		raise HTTPException(status_code = 400, detail = "Missing filename.")

	try:
		upload_info = await service.handle_initial_upload(file)
		extension = Path(upload_info["original_filename"]).suffix
		final_filename = f"{user_id}/{uuid.uuid4().hex}{extension}"
		message_type = MessageType.image if (upload_info["mime_type"] or "").startswith("image/") else MessageType.file

		schema = FileMessageCreate.model_validate(
			{
				"user_id":user_id,
				"device":device,
				"type":message_type,
				"file_size":upload_info["size_bytes"],
				"file_type":upload_info["mime_type"] or "application/octet-stream",
				"file_name":upload_info["original_filename"],
				"file_path":final_filename
			}
		)
		message = await service.finalize_file_message(
			schema = schema,
			temp_filename = upload_info["temp_filename"],
			file_size = upload_info["size_bytes"],
		)
		message_id = _extract_message_id(message)
		await ws_manager.broadcast_to_user(
			user_id,
			{"event":"message.updated", "message_id":message_id},
		)
		return message
	except QuotaExceededError as exc:
		raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = str(exc)) from exc
	except (FileUploadAbortedError, FilePathNotFoundError, MessagePermissionError) as exc:
		raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(exc)) from exc


@router.get("/{message_id}/download")
async def download_file(
		message_id: int,
		token: str | None = Query(None),
		authorization: str | None = Header(None),
		file_repo: FileRepo = Depends(get_file_repo),
		service: FileService = Depends(get_file_service),
):
	"""Download file by message id with owner permission check."""
	user_id = _resolve_request_user_id(token = token, authorization = authorization)
	try:
		message = await service.get_file_for_user(message_id = message_id, user_id = user_id)
	except Exception as exc:
		raise HTTPException(status_code = 404, detail = "File not found") from exc

	if not message.file_path:
		raise HTTPException(status_code = 404, detail = "File not found.")

	return await _file_response(file_repo, message.file_path, as_download = True, download_name = message.file_name)


@router.get("/{message_id}/view")
async def view_file(
		message_id: int,
		token: str | None = Query(None),
		authorization: str | None = Header(None),
		file_repo: FileRepo = Depends(get_file_repo),
		service: FileService = Depends(get_file_service),
):
	"""Inline preview endpoint (image messages only)."""
	user_id = _resolve_request_user_id(token = token, authorization = authorization)
	try:
		message = await service.get_file_for_user(message_id = message_id, user_id = user_id)
	except Exception as exc:
		raise HTTPException(status_code = 404, detail = "File not found") from exc

	if message.type != MessageType.image:
		raise HTTPException(status_code = 415, detail = "Preview is only available for image messages.")

	if not message.file_path:
		raise HTTPException(status_code = 404, detail = "File not found.")

	return await _file_response(file_repo, message.file_path, as_download = False)


@router.delete("/{message_id}")
async def delete_message(
		message_id: int,
		user_id: int = Depends(get_current_user_id),
		service: MessageService = Depends(get_message_service),
):
	"""Delete message and emit realtime delete event."""
	await service.delete_message(message_id = message_id, user_id = user_id)
	await ws_manager.broadcast_to_user(
		user_id,
		{"event":"message.deleted", "message_id":message_id},
	)
	return {"status":"success", "message":"Message deleted"}
