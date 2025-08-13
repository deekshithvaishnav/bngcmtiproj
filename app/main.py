from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
from app.db.session import engine
from app.db.base import Base
# Ensure tables exist if running without Alembic (dev convenience)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS] if isinstance(settings.CORS_ORIGINS, str) else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"]
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "Router test passed"}

@app.get("/health")
def health():
    return {"status": "ok"}