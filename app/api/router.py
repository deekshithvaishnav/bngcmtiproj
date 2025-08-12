from fastapi import APIRouter
from app.api.v1 import auth, officer, supervisor, operator, notifications
from app.api.v1.auth import router as auth
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(officer.router, prefix="/officer", tags=["officer"])
# api_router.include_router(supervisor.router, prefix="/supervisor", tags=["supervisor"])
# api_router.include_router(operator.router, prefix="/operator", tags=["operator"])
# api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])