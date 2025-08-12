from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base
from app.models.enums import UserRole

class RoleLock(Base):
	__tablename__ = "role_locks"
	id = Column(Integer, primary_key=True, index=True)
	role = Column(Enum(UserRole), nullable=False, index=True)
	session_id = Column(String(64), nullable=False, index=True)
	locked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
