from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    message_type = Column(String)  # 'text'/'image'/'file'
    created_at = Column(DateTime(timezone=True), server_default=func.now())