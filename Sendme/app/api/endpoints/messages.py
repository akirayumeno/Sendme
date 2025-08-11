from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.message import Message
from app.schemas.message import MessageCreate, Message as MessageSchema
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=MessageSchema)
def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    db_message = Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@router.get("/", response_model=List[MessageSchema])
def read_messages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return db.query(Message).offset(skip).limit(limit).all()