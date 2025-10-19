import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import models
from app.schemas import schemas


def get_message(db: Session, message_id: str):
	return db.query(models.Message).filter(models.Message.id == message_id).first()


def get_messages(db: Session, skip: int = 0, limit: int = 100):
	return db.query(models.Message).order_by(models.Message.created_at).offset(skip).limit(limit).all()


def create_text_message(db: Session, message: schemas.TextMessageCreate):
	db_message = models.Message(
		id = uuid.uuid4(),
		type = message.type,
		content = message.content,
		device = message.device,
		status = models.MessageStatus.success,
		created_at = datetime.now(timezone.utc)
	)
	db.add(db_message)
	db.commit()
	db.refresh(db_message)
	return db_message


def create_file_message(db: Session, message: schemas.FileMessageCreate):
	db_message = models.Message(
		id = uuid.uuid4(),
		type = message.type,
		file_name = message.fileName,
		file_size = message.fileSize,
		file_type = message.fileType,
		file_path = message.filePath,
		device = message.device,
		status = models.MessageStatus.success,
		created_at = datetime.now(timezone.utc)
	)
	db.add(db_message)
	db.commit()
	db.refresh(db_message)
	return db_message


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
