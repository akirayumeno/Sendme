from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.sendme_db import get_db, Device

router = APIRouter()


class DeviceCreate(BaseModel):
    id: str
    name: str


class DeviceResponse(BaseModel):
    id: str
    name: str
    last_seen: datetime
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[DeviceResponse])
async def get_devices(db: Session = Depends(get_db)):
    """获取设备列表"""
    devices = db.query(Device).all()
    return devices


@router.post("/", response_model=DeviceResponse)
async def register_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """注册设备"""

    # 检查设备是否已存在
    existing_device = db.query(Device).filter(Device.id == device.id).first()
    if existing_device:
        # 更新最后seen时间
        existing_device.last_seen = datetime.utcnow()
        db.commit()
        return existing_device

    # 创建新设备
    db_device = Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.put("/{device_id}/heartbeat")
async def device_heartbeat(device_id: str, db: Session = Depends(get_db)):
    """设备心跳"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.last_seen = datetime.utcnow()
    db.commit()
    return {"message": "Heartbeat updated"}


# routers/auth.py (简化版JWT认证)
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class DeviceLogin(BaseModel):
    device_id: str
    device_name: str


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/login", response_model=Token)
async def login_device(device: DeviceLogin):
    """设备登录，获取JWT token"""
    access_token = create_access_token(
        data={"device_id": device.device_id, "device_name": device.device_name}
    )
    return {"access_token": access_token, "token_type": "bearer"}