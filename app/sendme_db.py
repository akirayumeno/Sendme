from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/sendme")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 数据库模型
class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    last_seen = Column(DateTime, default=datetime)
    created_at = Column(DateTime, default=datetime)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, nullable=False)
    type = Column(String, nullable=False)  # text, image, file
    content = Column(Text)
    file_name = Column(String)
    file_size = Column(Integer)
    file_path = Column(String)
    timestamp = Column(DateTime, default=datetime)
    synced = Column(Boolean, default=False)


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    original_name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    mimetype = Column(String)
    size = Column(Integer)
    path = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime)


# 依赖注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
