from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
import asyncio
import uuid

from app.database import get_db
from app.schemas import schemas
from app.api import crud
from app.services.file_service import FileService

router_messages = APIRouter(
    prefix="/messages",
    tags=["messages"]
)

file_service = FileService()

@router_messages.post("/text", response_model=schemas.MessageResponse)
async def create_text_message(
       message: schemas.TextMessageCreate,
       db: Session = Depends(get_db)
):
    """Create a text message"""
    db_message = crud.create_text_message(db, message)
    return db_message


@router_messages.post("/upload", response_model=schemas.MessageResponse)
async def upload_file(
       file: UploadFile = File(...),
       device: schemas.DeviceType = schemas.DeviceType.desktop,
       db: Session = Depends(get_db)
):
    """Upload a file and create a file/image message"""
    try:
       file_info = await file_service.upload_file(file)

       if file.content_type.startswith("image/"):
           message_type = schemas.MessageType.image
       else:
           message_type = schemas.MessageType.file

       message_data = schemas.FileMessageCreate(
          type=message_type,
          fileName=file.filename,
          fileSize=file_info["size"],
          fileType=file.content_type,
          filePath=file_info["path"],
          device=device
       )

       db_message = crud.create_file_message(db, message_data)
       return db_message

    except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@router_messages.get("/", response_model=List[schemas.MessageResponse])
async def get_messages(
       skip: int = 0,
       limit: int = 100,
       db: Session = Depends(get_db)
):
    """Get all messages with pagination"""
    messages = crud.get_messages(db, skip=skip, limit=limit)
    return messages


@router_messages.get("/{message_id}", response_model=schemas.MessageResponse)
async def get_message(message_id: str, db: Session = Depends(get_db)):
    """Get a specific message by ID"""
    message = crud.get_message(db, message_id)
    if not message:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message


@router_messages.delete("/{message_id}")
async def delete_message(message_id: str, db: Session = Depends(get_db)):
    """Delete a message"""
    success = crud.delete_message(db, message_id)
    if not success:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

@router_messages.get("/files/{file_path:path}")
async def get_file(file_path: str):
    """Serve uploaded files"""
    return await file_service.get_file(file_path)

@router_messages.post("/simulate-upload")
async def simulate_upload(file_info: schemas.SimulateUploadRequest):
    """Simulate file upload with progress updates"""
    message_id = str(uuid.uuid4())
    for progress in range(0, 101, 20):
       await asyncio.sleep(0.1)
    return {"message_id": message_id, "status": "completed"}