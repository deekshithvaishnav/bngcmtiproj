from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ToolUsageShortOut(BaseModel):
	id: int
	tool_id: int
	user_id: int
	status: str

class ToolUsageCreateIn(BaseModel):
	tool_id: int
	user_id: int

class ApproveToolUsageOut(BaseModel):
	id: int
	tool_id: int
	user_id: int
	status: str
	approved_by: Optional[int] = None
	approved_at: Optional[datetime] = None
