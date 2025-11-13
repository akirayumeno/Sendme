import uuid
from datetime import timedelta, timezone, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import ACCESS_TOKEN_EXPIRE_MINUTES
from app.models import file_repository
from app.models import models
from app.models.file_repository import get_user, get_password_hash, verify_password, create_access_token, \
	get_current_user
from app.models.models import User, Message
from app.schemas import schemas
from app.schemas.schemas import UserSchema, UserCreate, Token
from app.services.file_service import FileService

router_messages = APIRouter(
	tags = ["messages"]
)

file_service = FileService()


@router_messages.post("/text", response_model = schemas.MessageResponse)
async def create_text_message(
		message: schemas.TextMessageCreate,
		db: Session = Depends(get_db),
		current_user: User = Depends(get_current_user)
):
	"""Create a text message"""
	db_message = file_repository.create_text_message(db, message, current_user)
	return db_message


@router_messages.put("/{message_id}", response_model = schemas.MessageResponse)
async def update_message(
		message_id: str,
		message: schemas.TextMessageCreate,
		db: Session = Depends(get_db)
):
	updated_message = file_repository.update_message(db, message_id, message)
	if not updated_message:
		raise HTTPException(status_code = 404, detail = "Message not found")

	return updated_message


@router_messages.post("/upload", response_model = schemas.MessageResponse)
async def upload_file(
		file: UploadFile = File(...),
		device: schemas.DeviceType = schemas.DeviceType.desktop,
		db: Session = Depends(get_db),
		current_user: User = Depends(get_current_user)
):
	"""Upload a file and create a file/image message"""
	try:
		file_info = await file_service.upload_file(file)

		if file.content_type.startswith("image/"):
			message_type = schemas.MessageType.image
		else:
			message_type = schemas.MessageType.file

		message_data = Message(
			id = uuid.uuid4(),
			user_id = current_user.id,
			type = message_type,
			file_name = file.filename,
			file_size = file_info["size"],
			file_type = file.content_type,
			file_path = file_info["path"],
			device = device,
			status = models.MessageStatus.success,
			created_at = datetime.now(timezone.utc)
		)

		db_message = file_repository.create_file_message(db, message_data)
		return db_message

	except Exception as e:
		raise HTTPException(status_code = 500, detail = str(e))


@router_messages.get("/", response_model = List[schemas.MessageResponse])
async def get_messages(
		skip: int = 0,
		limit: int = 100,
		db: Session = Depends(get_db),
		current_user: User = Depends(get_current_user)
):
	"""Get all messages with pagination"""
	messages = file_repository.get_messages(db, skip = skip, limit = limit, current_user = current_user)
	return messages


@router_messages.get("/{message_id}", response_model = schemas.MessageResponse)
async def get_message(message_id: str, db: Session = Depends(get_db)):
	"""Get a specific message by ID"""
	message = file_repository.get_message(db, message_id)
	if not message:
		raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Message not found")
	return message


@router_messages.delete("/{message_id}")
async def delete_message(message_id: str, db: Session = Depends(get_db)):
	"""Delete a message"""
	success = file_repository.delete_message(db, message_id)
	if not success:
		raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Message not found")


@router_messages.get("/download/{file_path:path}")
async def get_file(file_path: str):
	"""Serve uploaded files"""
	return await file_service.get_file(file_path)


@router_messages.get("/view/{file_path:path}")
async def get_image(file_path: str):
	"""Serve uploaded images"""
	return await file_service.get_image(file_path)


# Authentication Routes (/api/v1/auth/...)
@router_messages.post("/auth/register", response_model = UserSchema, status_code = status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
	"""
	User registration endpoint: /api/v1/auth/register
	"""
	db_user = get_user(db, username = user.username)
	if db_user:
		raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Username already registered")

	hashed_password = get_password_hash(user.password)
	db_user = User(username = user.username, hashed_password = hashed_password)
	db.add(db_user)
	db.commit()
	db.refresh(db_user)
	return db_user


@router_messages.post("/auth/token", response_model = Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
	"""
	Login endpoint: /api/v1/auth/token (Generates JWT)
	"""
	user = get_user(db, username = form_data.username)
	if not user or not verify_password(form_data.password, user.hashed_password):
		raise HTTPException(
			status_code = status.HTTP_401_UNAUTHORIZED,
			detail = "Incorrect username or password",
			headers = {"WWW-Authenticate":"Bearer"},
		)

	access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
	access_token = create_access_token(
		data = {"sub":user.username}, expires_delta = access_token_expires
	)
	return {"access_token":access_token, "token_type":"bearer"}
