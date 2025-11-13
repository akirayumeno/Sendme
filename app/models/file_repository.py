import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException
from fastapi.params import Depends
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from starlette import status

from app.database import get_db
from app.main import pwd_context, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM, oauth2_scheme
from app.models import models
from app.models.models import User, Message
from app.schemas import schemas
from app.schemas.schemas import TokenData


def get_message(db: Session, message_id: str):
	return db.query(models.Message).filter(models.Message.id == message_id).first()


def get_messages(db: Session, skip: int = 0, limit: int = 100, current_user = User):
	return db.query(models.Message).filter(models.Message.user_id == current_user.id).order_by(

		models.Message.created_at

	).offset(skip).limit(limit).all()


def create_text_message(db: Session, message: schemas.TextMessageCreate, current_user: User):
	db_message = models.Message(

		id = uuid.uuid4(),

		user_id = current_user.id,

		type = "text",

		content = message.content,

		device = message.device,

		status = models.MessageStatus.success,

		created_at = datetime.now(timezone.utc)

	)

	db.add(db_message)

	db.commit()

	db.refresh(db_message)

	return db_message


def create_file_message(db: Session, message: Message):
	db.add(message)

	db.commit()

	db.refresh(message)

	return message


def update_message(db: Session, message_id: str, new_message: schemas.TextMessageCreate):
	message = db.query(models.Message).filter(models.Message.id == message_id).first()

	if message:
		message.content = new_message.content

		message.updated_at = datetime.now(timezone.utc)

		db.add(message)

		db.commit()

		db.refresh(message)

		return message

	return False


def delete_message(db: Session, message_id: str):
	message = db.query(models.Message).filter(models.Message.id == message_id).first()

	if message:
		db.delete(message)

		db.commit()

		return True

	return False


# Authentication Logic Functions

def verify_password(plain_password, hashed_password):
	return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
	return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
	to_encode = data.copy()

	if expires_delta:
		expire = datetime.now(timezone.utc) + expires_delta

	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)

	to_encode.update({"exp":expire})

	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)

	return encoded_jwt


def get_user(db: Session, username: str):
	return db.query(User).filter(User.username == username).first()


# Dependency: Get Current Active User (Protected Route Logic)

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
	credentials_exception = HTTPException(

		status_code = status.HTTP_401_UNAUTHORIZED,

		detail = "Could not validate credentials",

		headers = {"WWW-Authenticate":"Bearer"},

	)

	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])

		username: str = payload.get("sub")

		if username is None:
			raise credentials_exception

		token_data = TokenData(username = username)

	except JWTError:
		raise credentials_exception

	user = get_user(db, username = token_data.username)

	if user is None:
		raise credentials_exception

	return user
