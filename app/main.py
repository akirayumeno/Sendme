import uuid
import os
import shutil
import logging
import json
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import redis

from app.sendme_db import engine, Base
from app.routers import messages, files, devices, auth

UPLOAD_DIR = "uploads"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create db tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SendMe API", version="1.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files service
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

# Redis connection
try:
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    # Test connection
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None

# Include routers
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(files.router, prefix="/api/files", tags=["files"])


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.device_connections: dict = {}

    async def connect(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.device_connections[device_id] = websocket
        logger.info(f"Device {device_id} connected via WebSocket")

    def disconnect(self, websocket: WebSocket, device_id: str):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

        if device_id in self.device_connections:
            del self.device_connections[device_id]

        logger.info(f"Device {device_id} disconnected")

    async def broadcast_message(self, message: dict):
        disconnected = []
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            try:
                self.active_connections.remove(connection)
            except ValueError:
                pass

    async def send_to_device(self, device_id: str, message: dict):
        if device_id in self.device_connections:
            try:
                await self.device_connections[device_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Failed to send message to device {device_id}: {e}")
                return False
        return False


manager = ConnectionManager()


@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    await manager.connect(websocket, device_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)

                # Broadcast message to all connected devices
                await manager.broadcast_message({
                    "type": "new_message",
                    "data": message_data
                })

                # Save to Redis if available
                if redis_client:
                    try:
                        redis_client.lpush(f"messages:{device_id}", json.dumps(message_data))
                    except Exception as e:
                        logger.error(f"Redis save error: {e}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, device_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, device_id)


@app.get("/")
async def root():
    return {"message": "SendMe API is running!", "version": "1.0.0"}


@app.get("/data")
def get_data():
    return {"message": "Hello from backend", "status": "ok"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_status = "connected" if redis_client else "disconnected"
    return {
        "status": "healthy",
        "redis": redis_status,
        "upload_dir": UPLOAD_DIR,
        "active_connections": len(manager.active_connections)
    }


# File upload endpoint - changed from /upload to /api/upload for consistency
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file endpoint that matches the frontend expectation
    Returns: {"filename": str, "url": str, "size": int}
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Get file extension
        file_ext = os.path.splitext(file.filename)[1].lower()

        # Optional: Add file type validation
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.doc', '.docx', '.zip'}
        if file_ext not in allowed_extensions:
            logger.warning(f"Potentially unsafe file type: {file_ext}")

        # Generate safe filename
        safe_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)

        # Get file size
        file_size = 0

        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            file_size = len(content)
            buffer.write(content)

        # Generate URL for frontend
        file_url = f"/uploads/{safe_filename}"

        logger.info(f"File uploaded successfully: {safe_filename} ({file_size} bytes)")

        # Return response matching frontend expectation
        return {
            "filename": file.filename,  # Original filename
            "url": file_url,  # URL to access the file
            "path": file_path,  # Server file path (for internal use)
            "size": file_size,  # File size in bytes
            "safe_filename": safe_filename  # Generated safe filename
        }

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


# Optional: Add endpoint to delete files
@app.delete("/api/upload/{filename}")
async def delete_file(filename: str):
    """Delete uploaded file"""
    try:
        # Validate filename (should be UUID format)
        file_path = os.path.join(UPLOAD_DIR, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        os.remove(file_path)
        logger.info(f"File deleted: {filename}")

        return {"message": "File deleted successfully", "filename": filename}

    except Exception as e:
        logger.error(f"File deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")


# Optional: Get file info
@app.get("/api/upload/{filename}/info")
async def get_file_info(filename: str):
    """Get file information"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        file_stat = os.stat(file_path)

        return {
            "filename": filename,
            "size": file_stat.st_size,
            "created": file_stat.st_ctime,
            "modified": file_stat.st_mtime,
            "url": f"/uploads/{filename}"
        }

    except Exception as e:
        logger.error(f"Get file info failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get file info failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)