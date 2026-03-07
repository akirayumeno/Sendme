from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.router import router as message_router
from app.core.database import Base, engine
from app.core.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
	# Auto-create tables for local development convenience.
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
	yield


app = FastAPI(title = "SendMe API", version = "1.0.0", lifespan = lifespan)
register_exception_handlers(app)

app.include_router(auth_router, prefix = "/api/v1")
app.include_router(message_router, prefix = "/api/v1")

app.add_middleware(
	CORSMiddleware,
	allow_origins = [
		"http://localhost:3000",
		"http://localhost:5173",
	],
	allow_credentials = True,
	allow_methods = ["*"],
	allow_headers = ["*"],
)


@app.get("/")
async def root():
	return {"message":"SendMe API is running"}
