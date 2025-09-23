import asyncio
import uuid
from typing import List

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import engine
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

