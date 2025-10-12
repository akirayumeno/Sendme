from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import models
from app.schemas import schemas
import uuid

def get_message(db: Session, message_id: str):
    return db.query(models.Message).filter(models.Message.id == message_id).first()

def get_messages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Message).order_by(desc(models.Message.created_at)).offset(skip).limit(limit).all()

def create_text_message(db: Session, message: schemas.TextMessageCreate):
    db_message = models.Message(
        id=uuid.uuid4(),
        type=message.type,
        content=message.content,
        device=message.device,
        status=models.MessageStatus.success
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def create_file_message(db: Session, message: schemas.FileMessageCreate):
    db_message = models.Message(
        id=uuid.uuid4(),
        type=message.type,
        file_name=message.fileName,
        file_size=message.fileSize,
        file_type=message.fileType,
        file_path=message.filePath,
        device=message.device,
        status=models.MessageStatus.success
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def delete_message(db: Session, message_id: str):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if message:
        db.delete(message)
        db.commit()
        return True
    return False


# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - use environment variable or default to local PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://username:password@localhost:5432/sendme_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()