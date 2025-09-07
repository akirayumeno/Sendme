from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.sendme_db import get_db, Message

router = APIRouter()


class MessageCreate(BaseModel):
    device_id: str
    type: str
    content: str = None
    file_name: str = None
    file_size: int = None
    file_path: str = None


class MessageResponse(BaseModel):
    id: int
    device_id: str
    type: str
    content: str = None
    file_name: str = None
    file_size: int = None
    file_path: str = None
    timestamp: datetime
    synced: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[MessageResponse])
async def get_messages(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """获取消息列表"""
    messages = db.query(Message).order_by(Message.timestamp.desc()).offset(skip).limit(limit).all()
    return messages


@router.post("/", response_model=MessageResponse)
async def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    """创建新消息"""
    db_message = Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: int, db: Session = Depends(get_db)):
    """获取单个消息"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.delete("/{message_id}")
async def delete_message(message_id: int, db: Session = Depends(get_db)):
    """删除消息"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()
    return {"message": "Message deleted successfully"}
