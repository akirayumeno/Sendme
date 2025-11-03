from fastapi import FastAPI
# Libraries for JWT authentication and password hashing
from starlette.middleware.cors import CORSMiddleware

from app.api.messages import router_messages
from app.database import engine
from app.models import models

# JWT Settings
SECRET_KEY = "YOUR_SUPER_SECRET_KEY"  # Use a secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create tables
models.Base.metadata.create_all(bind = engine)

app = FastAPI(title = "SendMe API", version = "1.0.0")

app.include_router(router_messages, prefix = "/api/v1")

# CORS middleware
app.add_middleware(
	CORSMiddleware,
	allow_origins = ["http://localhost:3000"],
	allow_credentials = True,
	allow_methods = ["*"],
	allow_headers = ["*"],
)


@app.get("/")
async def root():
	return {"message":"SendMe API is running"}
