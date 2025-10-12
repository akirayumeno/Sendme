from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import asyncio
from datetime import datetime

from .database import get_db, engine
from . import models, schemas, crud
from .services.file_service import FileService

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SendMe API", version="1.0.0")

# CORS middleware
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:3000"],  # React dev server
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

file_service = FileService()


@app.get("/")
async def root():
	return {"message": "SendMe API is running"}


@app.post("/messages/text", response_model=schemas.MessageResponse)
async def create_text_message(
		message: schemas.TextMessageCreate,
		db: Session = Depends(get_db)
):
	"""Create a text message"""
	db_message = crud.create_text_message(db, message)
	return db_message


@app.post("/messages/upload", response_model=schemas.MessageResponse)
async def upload_file(
		file: UploadFile = File(...),
		device: str = "desktop",
		db: Session = Depends(get_db)
):
	"""Upload a file and create a file/image message"""
	try:
		# Upload file to storage (local or S3)
		file_info = await file_service.upload_file(file)

		# Determine message type
		message_type = "image" if file.content_type.startswith("image/") else "file"

		# Create message in database
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


@app.get("/messages", response_model=List[schemas.MessageResponse])
async def get_messages(
		skip: int = 0,
		limit: int = 100,
		db: Session = Depends(get_db)
):
	"""Get all messages with pagination"""
	messages = crud.get_messages(db, skip=skip, limit=limit)
	return messages


@app.get("/messages/{message_id}", response_model=schemas.MessageResponse)
async def get_message(message_id: str, db: Session = Depends(get_db)):
	"""Get a specific message by ID"""
	message = crud.get_message(db, message_id)
	if not message:
		raise HTTPException(status_code=404, detail="Message not found")
	return message


@app.delete("/messages/{message_id}")
async def delete_message(message_id: str, db: Session = Depends(get_db)):
	"""Delete a message"""
	success = crud.delete_message(db, message_id)
	if not success:
		raise HTTPException(status_code=404, detail="Message not found")
	return {"message": "Message deleted successfully"}


@app.get("/files/{file_path}")
async def get_file(file_path: str):
	"""Serve uploaded files"""
	return await file_service.get_file(file_path)


# Simulate upload progress endpoint (for demo purposes)
@app.post("/messages/simulate-upload")
async def simulate_upload(file_info: schemas.SimulateUploadRequest):
	"""Simulate file upload with progress updates"""
	# In a real app, this would be WebSocket or Server-Sent Events
	message_id = str(uuid.uuid4())

	# Simulate progress updates
	for progress in range(0, 101, 20):
		await asyncio.sleep(0.1)  # Simulate processing time
	# In real implementation, you'd emit progress to WebSocket

	return {"message_id": message_id, "status": "completed"}
