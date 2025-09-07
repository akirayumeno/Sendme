from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pathlib import Path

from app.sendme_db import get_db, File, Message

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 26214400))  # 25MB


@router.post("/upload")
async def upload_file(
        file: UploadFile = FastAPIFile(...),
        device_id: str = None,
        db: Session = Depends(get_db)
):
    """文件上传"""

    # 检查文件大小
    file_size = 0
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        )

    # 生成唯一文件名
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 保存文件
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    # 保存文件信息到数据库
    db_file = File(
        original_name=file.filename,
        filename=unique_filename,
        mimetype=file.content_type,
        size=file_size,
        path=file_path,
        uploaded_by=device_id or "unknown"
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # 创建消息记录
    message_type = "image" if file.content_type.startswith("image/") else "file"
    db_message = Message(
        device_id=device_id or "unknown",
        type=message_type,
        content=f"/uploads/{unique_filename}",
        file_name=file.filename,
        file_size=file_size,
        file_path=file_path
    )
    db.add(db_message)
    db.commit()

    return {
        "message": "File uploaded successfully",
        "file_id": db_file.id,
        "filename": unique_filename,
        "original_name": file.filename,
        "size": file_size,
        "url": f"/uploads/{unique_filename}"
    }


@router.get("/download/{filename}")
async def download_file(filename: str, db: Session = Depends(get_db)):
    """文件下载"""
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # 从数据库获取文件信息
    db_file = db.query(File).filter(File.filename == filename).first()
    original_name = db_file.original_name if db_file else filename

    return FileResponse(
        path=file_path,
        filename=original_name,
        media_type='application/octet-stream'
    )


@router.get("/{file_id}")
async def get_file_info(file_id: int, db: Session = Depends(get_db)):
    """获取文件信息"""
    file_info = db.query(File).filter(File.id == file_id).first()
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    return file_info