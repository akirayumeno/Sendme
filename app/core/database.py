# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.settings import Settings

# Database URL - use environment variable or default to local PostgreSQL
DATABASE_URL = Settings.DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args = {"options":"-c timezone=utc"})
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base = declarative_base()


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
