# app/database.py
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL - use environment variable or default to local PostgreSQL
DATABASE_URL = os.getenv(
	"DATABASE_URL",
	"postgresql://postgres:password@localhost:5432/sendme_db"
)

engine = create_engine(DATABASE_URL, connect_args = {"options":"-c timezone=utc"})
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base = declarative_base()


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
