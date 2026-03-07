import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from starlette import status

from app.core.dependencies import get_current_user_id, get_file_repo, get_file_service, get_message_service
from app.core.enums import DeviceType, MessageType
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


def _resolve_file_path(file_repo: FileRepo, relative_path: str) -> Path:
	full_path = (file_repo.upload_dir / relative_path).resolve()
	upload_root = file_repo.upload_dir.resolve()
	if upload_root not in full_path.parents:
		raise HTTPException(status_code = 400, detail = "Invalid file path.")
	return full_path


def _file_response(file_repo: FileRepo, relative_path: str, as_download: bool) -> FileResponse:
	full_path = _resolve_file_path(file_repo, relative_path)
	if not full_path.exists():
		raise HTTPException(status_code = 404, detail = "File not found.")
	filename = os.path.basename(relative_path) if as_download else None
	return FileResponse(path = str(full_path), filename = filename)


@router.post("/text", response_model = MessageResponse)
async def send_text(
		payload: TextMessageRequest,
		user_id: int = Depends(get_current_user_id),
		service: MessageService = Depends(get_message_service),
):
	schema = TextMessageCreate(
		user_id = user_id,
		content = payload.content,
		type = MessageType.text,
		device = payload.device,
	)
	return await service.create_text_message(schema)


@router.get("/history", response_model = list[MessageResponse])
async def get_history(
		page: int = Query(1, ge = 1),
		user_id: int = Depends(get_current_user_id),
		service: MessageService = Depends(get_message_service),
):
	return await service.get_history(user_id = user_id, page = page)


@router.post("/upload", response_model = MessageResponse)
async def upload_file(
		file: UploadFile = File(...),
		device: DeviceType = Form(DeviceType.desktop),
		user_id: int = Depends(get_current_user_id),
		service: FileService = Depends(get_file_service),
):
	if not file.filename:
		raise HTTPException(status_code = 400, detail = "Missing filename.")

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

	try:
		return await service.finalize_file_message(
			schema = schema,
			temp_filename = upload_info["temp_filename"],
			file_size = upload_info["size_bytes"],
		)
	except QuotaExceededError as exc:
		raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = str(exc)) from exc
	except (FileUploadAbortedError, FilePathNotFoundError, MessagePermissionError) as exc:
		raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(exc)) from exc


@router.get("/{message_id}/download")
async def download_file(
		message_id: int,
		user_id: int = Depends(get_current_user_id),
		file_repo: FileRepo = Depends(get_file_repo),
		service: FileService = Depends(get_file_service),
):
	file_path = await service.get_file_path_for_user(message_id = message_id, user_id = user_id)
	return _file_response(file_repo, file_path, as_download = True)


@router.get("/{message_id}/view")
async def view_file(
		message_id: int,
		user_id: int = Depends(get_current_user_id),
		file_repo: FileRepo = Depends(get_file_repo),
		service: FileService = Depends(get_file_service),
):
	file_path = await service.get_file_path_for_user(message_id = message_id, user_id = user_id)
	return _file_response(file_repo, file_path, as_download = False)


@router.delete("/{message_id}")
async def delete_message(
		message_id: int,
		user_id: int = Depends(get_current_user_id),
		service: MessageService = Depends(get_message_service),
):
	await service.delete_message(message_id = message_id, user_id = user_id)
	return {"status":"success", "message":"Message deleted"}
