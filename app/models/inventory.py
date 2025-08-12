from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class ToolInventory(Base):
	__tablename__ = "tool_inventory"
	id = Column(Integer, primary_key=True, index=True)
	tool_name = Column(String(100), nullable=False)
	quantity = Column(Integer, nullable=False, default=0)
	added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
