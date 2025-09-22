import asyncio
import uuid
from typing import List

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import engine, get_db, create_file_message
from app.api import router
from app.models import models
from app.schemas import schemas
from app.services.file_service import FileService

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

# loading routes
app.include_router(router)
@app.get("/")
async def root():
	return {"message": "SendMe API is running"}

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
