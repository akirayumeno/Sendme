import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.router import router as message_router
from app.api.ws import router as ws_router
from app.core.database import Base, SessionLocal, engine
from app.core.exception_handlers import register_exception_handlers
from app.core.settings import settings
from app.services.file_service import FileService
from app.services.message_service import MessageService
from app.storage.file_repo import FileRepo
from app.storage.redis_repo import RedisRepo
from app.storage.sqlalchemy_repo import MessageRepository, UserRepository

logger = logging.getLogger(__name__)


async def _expired_message_cleanup_loop(stop_event: asyncio.Event):
	while not stop_event.is_set():
		try:
			async with SessionLocal() as db:
				message_repo = MessageRepository(db)
				user_repo = UserRepository(db)
				redis_repo = RedisRepo(settings.REDIS_URL)
				file_repo = FileRepo(upload_dir = Path(settings.UPLOAD_DIR))
				file_service = FileService(
					file_repo = file_repo,
					message_repo = message_repo,
					user_repo = user_repo,
					redis_repo = redis_repo,
				)
				message_service = MessageService(
					message_repo = message_repo,
					user_repo = user_repo,
					file_service = file_service,
					redis_repo = redis_repo,
				)
				cleaned = await message_service.cleanup_expired_messages(limit = 200)
				if cleaned:
					logger.info("Expired message cleanup removed %s messages", cleaned)
		except Exception:
			logger.exception("Expired message cleanup failed")

		try:
			await asyncio.wait_for(stop_event.wait(), timeout = 60)
		except asyncio.TimeoutError:
			continue


@asynccontextmanager
async def lifespan(_: FastAPI):
	# Auto-create tables for local development convenience.
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
	stop_event = asyncio.Event()
	cleanup_task = asyncio.create_task(_expired_message_cleanup_loop(stop_event))
	yield
	stop_event.set()
	cleanup_task.cancel()
	try:
		await cleanup_task
	except asyncio.CancelledError:
		pass


app = FastAPI(title = "SendMe API", version = "1.0.0", lifespan = lifespan)
register_exception_handlers(app)

app.include_router(auth_router, prefix = "/api/v1")
app.include_router(message_router, prefix = "/api/v1")
app.include_router(ws_router, prefix = "/api/v1")

app.add_middleware(
	CORSMiddleware,
	allow_origins = [
		"http://localhost:3000",  # local React development port
		"https://send-me.dev",  # frontend domain
		"https://www.send-me.dev",  # www domain
	],
	allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?$",
	allow_credentials = True,
	allow_methods = ["*"],
	allow_headers = ["*"],
)


@app.get("/")
async def root():
	return {"message":"SendMe API is running"}
