from sqlalchemy import create_engine
from sqlalchemy.orm import Session as OrmSessionmaker
from app.core.config import settings

engine = create_engine(settings.db_url(), pool_pre_ping=True, future=True)

SessionLocal = OrmSessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()