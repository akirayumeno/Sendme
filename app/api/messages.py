from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.models import Message

router_message = APIRouter(prefix="/api/v1/messages", tags=["messages"])

# Request model to data receiving
class MessageCreate(BaseModel):
    device_id: str
    type: str
    content: str = None
    file_name: str = None
    file_size: int = None
    file_path: str = None

# Response model to frontend, preventing data leak
class MessageResponse(BaseModel):
    id: UUID
    device_id: str
    type: str
    content: str = None
    file_name: str = None
    file_size: int = None
    file_path: str = None
    created_at: datetime

    class Config:
        from_attributes = True


@router_message.get("/", response_model=List[MessageResponse])
async def get_messages(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    # get messages
    messages = db.query(Message).order_by(Message.updated_at.desc()).offset(skip).limit(limit).all()
    return messages


@router_message.post("/", response_model=MessageResponse)
async def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    # create new message
    db_message = Message(**message.model_dump())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@router_message.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: int, db: Session = Depends(get_db)):
    # get a single message
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router_message.delete("/{message_id}")
async def delete_message(message_id: int, db: Session = Depends(get_db)):
    #  delete a certain message
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()
    return {"message": "Message deleted successfully"}
